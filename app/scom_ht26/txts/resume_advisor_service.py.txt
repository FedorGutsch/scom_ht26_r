from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import Any
from urllib.parse import quote_plus

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout
from sqlalchemy.orm import Session, undefer

from app.config import settings
from app.models.resume_advisor import (
    ErrorPayload,
    FrontendLink,
    FrontendSection,
    RelatedRole,
    ResumeAdviceData,
    ResumeAdviceFrontend,
    ResumeAdviceRequest,
    ResumeAdviceResponse,
)
from app.prompts.resume_advisor import SYSTEM_PROMPT, build_user_prompt
from app.schemas.candidate_base import Candidate

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_PROVIDER = "openrouter"

ErrorHandler = Callable[[ErrorPayload], None]


class ResumeAdvisorService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.timeout_seconds = settings.OPENROUTER_TIMEOUT_SECONDS

    def analyze_resume(
        self,
        payload: ResumeAdviceRequest,
        on_error: ErrorHandler | None = None,
    ) -> ResumeAdviceResponse:
        if not self.api_key:
            return self._fail(
                code="missing_api_key",
                message="Не задан OPENROUTER_API_KEY.",
                on_error=on_error,
            )

        try:
            resume_text = self._resolve_resume_text(payload)
            completion = self.send_chat_request(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": build_user_prompt(
                            resume_text=resume_text,
                            target_role=payload.target_role,
                        ),
                    },
                ]
            )
            content = self._extract_message_content(completion)
            parsed = self._parse_model_json(content)

            summary = str(parsed.get("summary", "")).strip()
            strengths = self._normalize_string_list(parsed.get("strengths", []))
            gaps = self._normalize_string_list(parsed.get("gaps", []))
            searches = self._normalize_searches(parsed.get("recommended_searches", []))
            related_roles = self._normalize_related_roles(parsed.get("related_roles", []))

            return ResumeAdviceResponse(
                success=True,
                data=ResumeAdviceData(
                    summary=summary,
                    strengths=strengths,
                    gaps=gaps,
                    recommended_searches=searches,
                    related_roles=related_roles,
                    frontend=self._build_frontend_payload(summary, strengths, gaps, searches),
                    model=self.model,
                    provider=OPENROUTER_PROVIDER,
                ),
                error=None,
            )
        except Timeout as exc:
            return self._fail("timeout", "Модель не ответила за отведенное время.", on_error, str(exc))
        except RequestException as exc:
            return self._fail("network_error", "Ошибка сети при обращении к OpenRouter.", on_error, str(exc))
        except json.JSONDecodeError as exc:
            return self._fail("invalid_json", "Модель вернула некорректный JSON.", on_error, str(exc))
        except ValueError as exc:
            return self._fail("invalid_response", "Не удалось обработать ответ модели.", on_error, str(exc))
        except Exception as exc:
            return self._fail("unexpected_error", "Непредвиденная ошибка во время анализа резюме.", on_error, str(exc))

    def send_chat_request(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
    ) -> dict[str, Any] | Iterable[str]:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=self._build_headers(),
            json={
                "model": self.model,
                "messages": messages,
                "stream": stream,
            },
            timeout=self.timeout_seconds,
            stream=stream,
        )
        response.raise_for_status()

        if stream:
            return self._stream_text_chunks(response)

        return response.json()

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": settings.PROJECT_NAME,
        }

    def _stream_text_chunks(self, response: Response) -> Iterable[str]:
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line or not raw_line.startswith("data:"):
                continue

            payload = raw_line[5:].strip()
            if payload == "[DONE]":
                break

            chunk = json.loads(payload)
            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
            if content:
                yield content

    def _resolve_resume_text(self, payload: ResumeAdviceRequest) -> str:
        if payload.resume_text and payload.resume_text.strip():
            return payload.resume_text.strip()

        if payload.candidate_id is None:
            raise ValueError("Нужно передать либо resume_text, либо candidate_id.")

        if self.db is None:
            raise ValueError("Для поиска резюме по candidate_id требуется DB session.")

        candidate = (
            self.db.query(Candidate)
            .options(undefer(Candidate.resume))
            .filter(Candidate.id == payload.candidate_id)
            .one_or_none()
        )
        if candidate is None:
            raise ValueError(f"Кандидат {payload.candidate_id} не найден.")
        if not candidate.resume or not candidate.resume.strip():
            raise ValueError(f"У кандидата {payload.candidate_id} отсутствует текст резюме.")
        return candidate.resume.strip()

    def _extract_message_content(self, completion: dict[str, Any]) -> str:
        try:
            return completion["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("В ответе модели отсутствует message.content.") from exc

    def _parse_model_json(self, content: str) -> dict[str, Any]:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        return json.loads(cleaned)

    def _normalize_string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("Ожидался список строк.")
        return [str(item).strip() for item in value if str(item).strip()]

    def _normalize_searches(self, value: Any) -> list[str]:
        return self._normalize_string_list(value)[:5]

    def _normalize_related_roles(self, value: Any) -> list[RelatedRole]:
        if not isinstance(value, list):
            raise ValueError("Ожидался список related_roles.")

        normalized: list[RelatedRole] = []
        for item in value[:5]:
            if not isinstance(item, dict):
                raise ValueError("Элемент related_roles должен быть объектом.")

            role_title = str(item.get("role_title", "")).strip()
            relevance_reason = str(item.get("relevance_reason", "")).strip()
            search_hint = str(item.get("search_hint", "")).strip()
            if not role_title or not relevance_reason:
                continue

            query = search_hint or role_title
            normalized.append(
                RelatedRole(
                    role_title=role_title,
                    relevance_reason=relevance_reason,
                    search_hint=query,
                    search_url=self._build_search_url(query),
                )
            )

        if not normalized:
            raise ValueError("Модель не вернула подходящих ролей.")
        return normalized

    def _build_frontend_payload(
        self,
        summary: str,
        strengths: list[str],
        gaps: list[str],
        searches: list[str],
    ) -> ResumeAdviceFrontend:
        return ResumeAdviceFrontend(
            headline=summary,
            sections=[
                FrontendSection(title="Сильные стороны", items=strengths),
                FrontendSection(title="Зоны роста", items=gaps),
            ],
            search_links=[
                FrontendLink(label=query, query=query, url=self._build_search_url(query))
                for query in searches
            ],
        )

    def _build_search_url(self, query: str) -> str:
        return f"https://hh.ru/search/vacancy?text={quote_plus(query)}"

    def _fail(
        self,
        code: str,
        message: str,
        on_error: ErrorHandler | None = None,
        details: str | None = None,
    ) -> ResumeAdviceResponse:
        error = ErrorPayload(code=code, message=message, details=details)
        if on_error is not None:
            on_error(error)
        return ResumeAdviceResponse(success=False, data=None, error=error)

from __future__ import annotations

import json
import re
import logging
import datetime
from collections.abc import Callable
from typing import Any

import requests
from requests.exceptions import RequestException, Timeout
from sqlalchemy.orm import Session, undefer

from app.config import settings
from app.models.resume_advisor import (
    ErrorPayload,
    ResumeAdviceData,
    ResumeAdviceRequest,
    ResumeAdviceResponse,
)
from app.prompts.resume_advisor import SYSTEM_PROMPT
from app.schemas.candidate_base import Candidate
from app.schemas.vacancy_base import Vacancy

# --- НАСТРОЙКА ЛОГГИРОВАНИЯ ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

llm_audit_logger = logging.getLogger("llm_audit")
llm_audit_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("llm_audit.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s\n%(message)s\n' + '='*80 + '\n'))
llm_audit_logger.addHandler(file_handler)

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
        # 1. Генерируем уникальное имя файла для этого конкретного запроса
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"llm_audit_{timestamp}_cand{payload.candidate_id}.log"
        
        # 2. Настраиваем временный обработчик файла для этого запроса
        current_audit_logger = logging.getLogger(f"audit_{timestamp}")
        handler = logging.FileHandler(log_filename, encoding="utf-8")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s\n' + '='*80 + '\n'))
        current_audit_logger.addHandler(handler)
        current_audit_logger.setLevel(logging.INFO)

        logger.info(f">>> Запуск анализа: Файл лога {log_filename}")


        try:
            # 1. Извлекаем данные из БД
            candidate = self.db.query(Candidate).options(undefer(Candidate.resume)).filter(Candidate.id == payload.candidate_id).one_or_none()
            vacancy = self.db.query(Vacancy).filter(Vacancy.id == payload.vacancy_id).one_or_none()

            if not candidate or not vacancy:
                return self._fail("not_found", "Данные не найдены в БД.", on_error)

            # 2. Логика просмотров
            actions = candidate.actions_history or []
            views_count = sum(1 for a in actions if a.get("action") == "просмотр" and str(a.get("vacancy_id")) == str(payload.vacancy_id))

            # 3. Формируем контекст
            db_articles = "- 'Как мы разработали ИИ-ассистента...' | URL: https://habr.com/ru/companies/sovcombank_technologies/articles/1023802/\n- 'Менторство новичка в ИТ...' | URL: https://habr.com/ru/companies/sovcombank_technologies/articles/1011814/"
            db_vacancies = "- Android-разработчик (Senior)\n- Data Engineer/Аналитик данных\n- DevSecOps-аналитик"

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"""
<VACANCY_REQUIREMENTS>
Должность: {vacancy.title}
Описание: {vacancy.description}
Требования: {vacancy.requirements}
</VACANCY_REQUIREMENTS>

<CANDIDATE_RESUME>
{candidate.resume}
</CANDIDATE_RESUME>

<VIEWS_COUNT>
{views_count}
</VIEWS_COUNT>

<DATABASE_ARTICLES>
{db_articles}
</DATABASE_ARTICLES>

<DATABASE_VACANCIES>
{db_vacancies}
</DATABASE_VACANCIES>
""".strip()}
            ]

            # Логируем запрос в файл
            current_audit_logger.info(f"REQUEST TO MODEL: {self.model}\nPROMPT:\n{json.dumps(messages, ensure_ascii=False, indent=2)}")

            # 4. Запрос к API
            completion = self.send_chat_request(messages)
            raw_content = completion["choices"][0]["message"]["content"]
            
            # --- ЛОГИРУЕМ ОТВЕТ В УНИКАЛЬНЫЙ ФАЙЛ ---
            current_audit_logger.info(f"RAW RESPONSE:\n{raw_content}")
            
            # Извлекаем контент и статистику
            raw_content = completion["choices"][0]["message"]["content"]
            usage = completion.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # Логируем статистику в консоль
            logger.info(f"Статистика API: Входных токенов: {prompt_tokens}, Выходных: {completion_tokens}, Всего: {total_tokens}")

            # Логируем ответ и статистику в файл
            llm_audit_logger.info(
                f"--- RAW RESPONSE FROM LLM ---\n{raw_content}\n\n"
                f"--- USAGE STATS ---\n"
                f"Prompt tokens: {prompt_tokens}\n"
                f"Completion tokens: {completion_tokens}\n"
                f"Total tokens: {total_tokens}"
            )

            # 5. Парсинг
            parsed_json = self._parse_json_from_tags(raw_content)

            # 6. Результат
            response_data = ResumeAdviceData(**parsed_json)
            logger.info("<<< Анализ успешно завершен.")
            return ResumeAdviceResponse(success=True, data=response_data, error=None)

        except Exception as exc:
            current_audit_logger.error(f"ERROR: {str(exc)}")
            return self._fail("processing_error", str(exc), on_error)
        finally:
            # Закрываем файл, чтобы его можно было сразу открыть в VS Code
            handler.close()
            current_audit_logger.removeHandler(handler)


    def send_chat_request(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Title": settings.PROJECT_NAME,
            },
            json={"model": self.model, "messages": messages},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def _parse_json_from_tags(self, text: str) -> dict[str, Any]:
        match = re.search(r"<JSON_RESPONSE>(.*?)</JSON_RESPONSE>", text, re.DOTALL)
        if not match:
            raise ValueError("Тег <JSON_RESPONSE> отсутствует в ответе модели.")
        
        json_str = match.group(1).strip()
        if json_str.startswith("```json"): json_str = json_str[7:]
        if json_str.endswith("```"): json_str = json_str[:-3]
        
        return json.loads(json_str.strip())

    def _fail(self, code: str, message: str, on_error: ErrorHandler | None = None) -> ResumeAdviceResponse:
        error = ErrorPayload(code=code, message=message)
        if on_error: on_error(error)
        return ResumeAdviceResponse(success=False, data=None, error=error)
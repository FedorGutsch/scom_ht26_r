from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class HabrArticle(BaseModel):
    title: str
    url: str

class CtaButton(BaseModel):
    text: str
    style: str
    icon: str
    search_query: Optional[str] = None

class AlternativeVacancy(BaseModel):
    title: str
    url: str



class RelatedRole(BaseModel):
    role_title: str
    relevance_reason: str
    search_hint: str
    search_url: str


class FrontendLink(BaseModel):
    label: str
    query: str
    url: str


class FrontendSection(BaseModel):
    title: str
    items: list[str]


class ResumeAdviceFrontend(BaseModel):
    headline: str
    sections: list[FrontendSection]
    search_links: list[FrontendLink]


class ResumeAdviceRequest(BaseModel):
    resume_text: str | None = Field(
        default=None,
        description="Текст резюме. Можно передать напрямую или получить по candidate_id.",
    )
    candidate_id: int | None = Field(
        default=None,
        description="ID кандидата, если нужно взять resume из базы.",
    )
    vacancy_id: int
    target_role: str | None = Field(default=None, description="Желаемая роль кандидата")

class RoadmapStep(BaseModel):
    step: int
    title: str
    description: str

class ResumeAdviceData(BaseModel):
    summary: str
    score: int
    metrics: Dict[str, int]
    matched_skills: List[str]
    missing_skills: List[str]
    history_insight: Optional[str] = None
    ctas: List[CtaButton]
    habr_article: Optional[HabrArticle] = None
    alternative_vacancies: Optional[List[AlternativeVacancy]] = None
    suggest_referral: bool
    career_roadmap: Optional[List[RoadmapStep]] = None


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: str | None = None


class ResumeAdviceResponse(BaseModel):
    success: bool
    data: ResumeAdviceData | None = None
    error: ErrorPayload | None = None

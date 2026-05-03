from pydantic import BaseModel, Field


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
    target_role: str | None = Field(default=None, description="Желаемая роль кандидата")


class ResumeAdviceData(BaseModel):
    summary: str
    strengths: list[str]
    gaps: list[str]
    recommended_searches: list[str]
    related_roles: list[RelatedRole]
    frontend: ResumeAdviceFrontend
    model: str
    provider: str


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: str | None = None


class ResumeAdviceResponse(BaseModel):
    success: bool
    data: ResumeAdviceData | None = None
    error: ErrorPayload | None = None

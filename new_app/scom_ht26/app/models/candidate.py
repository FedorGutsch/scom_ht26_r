from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ActionHistoryItem(BaseModel):
    vacancy_id: str
    action: str
    time: datetime

class CandidateCreate(BaseModel):
    resume: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experience_years: int = 0
    desired_salary: float = 0.0
    actions_history: list[ActionHistoryItem] = Field(default_factory=list)

class CandidateRead(CandidateCreate):
    id: int
    resume: Optional[str] = None  # Может быть None, если не загружено (deferred)
    
    model_config = ConfigDict(from_attributes=True)
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime

class VacancyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    conditions: Optional[str] = None
    responsibilities: Optional[str] = None
    status: Literal["Активная", "Архивная"] = "Активная"

class VacancyRead(VacancyCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
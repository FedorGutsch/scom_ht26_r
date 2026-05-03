from app.database.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text, JSON, Integer, Double


class Candidate(Base):
    __tablename__ = "сandidates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resume: Mapped[str] = mapped_column(Text, nullable=True, deferred=True)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    experience_years: Mapped[int] = mapped_column(Integer)
    desired_salary: Mapped[float] = mapped_column(Double)
    actions_history: Mapped[list[dict]] = mapped_column(JSON, default=list)

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    Text,
    Double,
    String,
    DateTime,
    CheckConstraint,
    func,
)
from datetime import datetime

from app.database.base import Base


class Vacancy(Base):
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    salary_min: Mapped[float] = mapped_column(Double)
    salary_max: Mapped[float] = mapped_column(Double)

    description: Mapped[str] = mapped_column(Text, nullable=True, deferred=True)
    requirements: Mapped[str] = mapped_column(Text, nullable=True, deferred=True)
    conditions: Mapped[str] = mapped_column(Text, nullable=True, deferred=True)
    responsibilities: Mapped[str] = mapped_column(Text, nullable=True, deferred=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Active")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('Активная', 'Архивная')", name="ck_vacancy_status" 
        ),
    )

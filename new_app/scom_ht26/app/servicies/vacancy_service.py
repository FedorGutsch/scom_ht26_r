from sqlalchemy.orm import Session, undefer
from sqlalchemy import select
from app.schemas.vacancy_base import Vacancy
from app.models.vacancy import VacancyCreate, VacancyRead
from app.exceptions import NotFoundException

class VacancyService:
    def __init__(self, db: Session):
        self.db = db

    def create(self,  VacancyCreate) -> VacancyRead:
        vacancy = Vacancy(**data.model_dump())
        self.db.add(vacancy)
        self.db.commit()
        self.db.refresh(vacancy)
        return VacancyRead.model_validate(vacancy)

    def get_by_id(self, vacancy_id: int, load_text_fields: bool = False) -> VacancyRead:
        stmt = select(Vacancy).where(Vacancy.id == vacancy_id)
        if load_text_fields:
            stmt = stmt.options(
                undefer(Vacancy.description),
                undefer(Vacancy.requirements),
                undefer(Vacancy.conditions),
                undefer(Vacancy.responsibilities),
            )
            
        vacancy = self.db.execute(stmt).scalar_one_or_none()
        if not vacancy:
            raise NotFoundException(f"Vacancy {vacancy_id} not found")
        return VacancyRead.model_validate(vacancy)

    def get_all(self, skip: int = 0, limit: int = 50) -> list[VacancyRead]:
        vacancies = self.db.query(Vacancy).offset(skip).limit(limit).all()
        return [VacancyRead.model_validate(v) for v in vacancies]
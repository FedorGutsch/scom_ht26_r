from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.servicies.vacancy_service import VacancyService
from app.models.vacancy import VacancyCreate, VacancyRead
from app.exceptions import NotFoundException

router = APIRouter(prefix="/vacancies", tags=["vacancies"])

@router.post("/", response_model=VacancyRead, status_code=201)
def create_vacancy(data: VacancyCreate, db: Session = Depends(get_db)):  # ← ИСПРАВЛЕНО: добавлено data:
    return VacancyService(db).create(data)

@router.get("/{vacancy_id}", response_model=VacancyRead)
def get_vacancy(
    vacancy_id: int,
    load_details: bool = Query(False, description="Загрузить отложенные текстовые поля"),
    db: Session = Depends(get_db)
):
    try:
        return VacancyService(db).get_by_id(vacancy_id, load_text_fields=load_details)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)

@router.get("/", response_model=list[VacancyRead])
def list_vacancies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return VacancyService(db).get_all(skip, limit)
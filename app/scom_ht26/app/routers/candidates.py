from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.servicies.candidate_service import CandidateService
from app.models.candidate import CandidateCreate, CandidateRead
from app.exceptions import NotFoundException

router = APIRouter(prefix="/candidates", tags=["candidates"])

@router.post("/", response_model=CandidateRead, status_code=201)
def create_candidate(data: CandidateCreate, db: Session = Depends(get_db)):  # ← ИСПРАВЛЕНО: добавлено data:
    return CandidateService(db).create(data)

@router.get("/{candidate_id}", response_model=CandidateRead)
def get_candidate(
    candidate_id: int, 
    load_resume: bool = Query(False, description="Загрузить отложенное поле resume"),
    db: Session = Depends(get_db)
):
    try:
        return CandidateService(db).get_by_id(candidate_id, load_resume=load_resume)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)

@router.get("/", response_model=list[CandidateRead])
def list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return CandidateService(db).get_all(skip, limit)
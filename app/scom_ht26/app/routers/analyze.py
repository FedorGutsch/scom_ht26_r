from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.resume_advisor import ResumeAdviceRequest, ResumeAdviceResponse
from app.servicies.resume_advisor_service import ResumeAdvisorService # Путь может отличаться

router = APIRouter(prefix="/analyze", tags=["AI"])

@router.post("/", response_model=ResumeAdviceResponse)
def analyze_candidate(request: ResumeAdviceRequest, db: Session = Depends(get_db)):
    service = ResumeAdvisorService(db)
    return service.analyze_resume(request)
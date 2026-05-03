from sqlalchemy.orm import Session, undefer
from sqlalchemy import select
from app.schemas.candidate_base import Candidate
from app.models.candidate import CandidateCreate, CandidateRead
from app.exceptions import NotFoundException

class CandidateService:
    def __init__(self, db: Session):
        self.db = db

    def create(self,  CandidateCreate) -> CandidateRead:
        candidate = Candidate(**data.model_dump())
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return CandidateRead.model_validate(candidate)

    def get_by_id(self, candidate_id: int, load_resume: bool = False) -> CandidateRead:
        stmt = select(Candidate).where(Candidate.id == candidate_id)
        if load_resume:
            stmt = stmt.options(undefer(Candidate.resume))  # Явно грузим deferred поле
            
        candidate = self.db.execute(stmt).scalar_one_or_none()
        if not candidate:
            raise NotFoundException(f"Candidate {candidate_id} not found")
        return CandidateRead.model_validate(candidate)

    def get_all(self, skip: int = 0, limit: int = 50) -> list[CandidateRead]:
        candidates = self.db.query(Candidate).offset(skip).limit(limit).all()
        return [CandidateRead.model_validate(c) for c in candidates]
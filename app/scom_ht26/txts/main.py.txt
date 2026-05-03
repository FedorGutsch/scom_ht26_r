from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.config import settings
from app.routers.candidates import router as candidates_router
from app.routers.vacancies import router as vacancies_router
from app.database.base import Base
from app.database.session import engine
from app.exceptions import AppException

def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, docs_url="/docs", redoc_url=None)

    # Авто-миграция для MVP
    Base.metadata.create_all(bind=engine)

    app.include_router(candidates_router, prefix=settings.API_PREFIX)
    app.include_router(vacancies_router, prefix=settings.API_PREFIX)

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    return app

app = create_app()
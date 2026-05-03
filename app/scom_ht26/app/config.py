from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore") # Добавили extra="ignore"
    
    PROJECT_NAME: str = "HireMatch MVP"
    DATABASE_URL: str = "sqlite:///./app.db"
    API_PREFIX: str = "/api/v1"
    
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "tencent/hy3-preview:free" # Или другая модель по умолчанию
    OPENROUTER_TIMEOUT_SECONDS: int = 30

settings = Settings()
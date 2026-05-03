from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)
    
    PROJECT_NAME: str = "HireMatch MVP"
    DATABASE_URL: str = "sqlite:///./app.db"
    API_PREFIX: str = "/api/v1"

settings = Settings()
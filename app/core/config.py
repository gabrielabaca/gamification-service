from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Gamification Service API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PORT: int = 9004
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "gamification_user"
    POSTGRES_PASSWORD: str = "gamification_password"
    POSTGRES_DB: str = "gamification_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    POINTS_TO_COINS_RATE: int = 100 

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

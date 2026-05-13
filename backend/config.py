from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    groq_api_key: str
    database_url: str = "sqlite+aiosqlite:///./partselect.db"
    chroma_db_path: str = "./chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    groq_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    cors_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

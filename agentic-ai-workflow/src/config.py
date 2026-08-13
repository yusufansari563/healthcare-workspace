import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Agentic AI Workflow"
    DEBUG: bool = True
    PORT: int = 8000
    
    # Database / LangGraph Postgres Persistence
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "agentic_workflow_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    
    # LLM Settings (Supports Ollama, OpenAI, Groq, OpenRouter)
    LLM_PROVIDER: str = "ollama"  # "ollama", "openai", "groq", "openrouter"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    
    # Optimization Settings
    MAX_TOKEN_LIMIT: int = 4096
    COMPRESS_PROMPTS: bool = True
    
    # 3rd Party Integrations
    CLICKUP_API_KEY: Optional[str] = None
    CLICKUP_LIST_ID: Optional[str] = None
    
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_REPO: Optional[str] = None  # e.g., "owner/repo"
    
    # Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    NOTIFICATION_EMAIL: str = "yusufansari563@gmail.com"
    
    # Vector DB / Local RAG
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_async_database_url(self) -> str:
        db_url = self.get_database_url()
        if db_url.startswith("postgresql://"):
            return db_url.replace("postgresql://", "postgresql+psycopg://")
        return db_url

settings = Settings()

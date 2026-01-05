"""
Application Configuration
Uses Pydantic Settings for environment variable management
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "GeneticFrames API"
    DEBUG: bool = True
    PORT: int = 8000
    
    # NCBI Entrez Configuration
    ENTREZ_EMAIL: str = "juliopc92@gmail.com"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080"
    ]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Redis Cache (Optional)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    # AlphaFold
    ALPHAFOLD_API_URL: str = "https://alphafold.ebi.ac.uk/api"
    ALPHAFOLD_ENABLED: bool = True
    
    # Supabase (Optional)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # S3/R2 Storage (Optional)
    S3_ENABLED: bool = False
    S3_BUCKET: str = "geneticframes"
    S3_REGION: str = "auto"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEBUG


# Create global settings instance
settings = Settings()

"""
Configuration module for the Document Copilot backend.

This module defines the Settings class which loads and validates environment
variables using Pydantic Settings. It serves as the single source of truth for
all configuration options in the application.
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the backend (d:\GAN_AI\agent_framwork\pydanticAi\document-copilot-t\backend)
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and/or .env file.
    """

    # --- Supabase Configuration ---
    SUPABASE_URL: str = Field(
        ...,
        description="The API URL of the Supabase project."
    )
    SUPABASE_ANON_KEY: str = Field(
        ...,
        description="The anonymous public key for the Supabase project."
    )
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        ...,
        description="The service role secret key (admin access) for the Supabase project."
    )

    # --- Postgres Database Configuration ---
    DATABASE_URL: str = Field(
        ...,
        description="Direct connection URL to the Supabase Postgres database (session pooler/direct connection)."
    )
    DATABASE_PASSWERD: str | None = Field(
        default=None,
        description="Password for the database (supports the typo key in local .env)."
    )

    # --- LLM Providers Configuration ---
    # Gemini / Google AI Settings
    GOOGLE_API_KEY: str | None = Field(
        default=None,
        description="API key for Google Gemini services."
    )
    GEMINI_EMBEDDING_MODEL: str = Field(
        default="gemini-embedding-2",
        description="The embedding model to use for Gemini."
    )
    GEMINI_EMBEDDING_DIMENSIONS: int = Field(
        default=1536,
        description="The dimensionality of the Gemini embeddings."
    )

    # OpenAI Settings (as fallback or alternative provider)
    OPENAI_API_KEY: str | None = Field(
        default=None,
        description="API key for OpenAI services."
    )
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="The embedding model to use for OpenAI."
    )
    OPENAI_EMBEDDING_DIMENSIONS: int = Field(
        default=1536,
        description="The dimensionality of the OpenAI embeddings."
    )

    # --- Server Configuration ---
    ALLOWED_ORIGINS: str = Field(
        ...,
        description="Comma-separated browser origins allowed to call the API (CORS)."
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """
        Parses the comma-separated ALLOWED_ORIGINS string into a list of strings.

        Returns:
            A list of trimmed, non-empty origin URLs.
        """
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Instantiate settings to validate and export on startup.
# This will fail fast if any required variables are missing or invalid.
settings = Settings()

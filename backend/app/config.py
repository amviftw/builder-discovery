from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env into os.environ so os.getenv works in model_post_init
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")


class Settings(BaseSettings):
    # GitHub
    github_tokens: list[str] = []

    # Gemini
    gemini_api_key: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/builder_discovery.db"

    # Server
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    # Cache
    cache_dir: str = str(Path(__file__).parent / "cache")

    # Discovery defaults
    default_country: str = "India"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def model_post_init(self, __context) -> None:
        # Parse GITHUB_TOKEN and GITHUB_TOKEN_2, GITHUB_TOKEN_3, etc.
        if not self.github_tokens:
            tokens = []
            main = os.getenv("GITHUB_TOKEN", "")
            if main:
                tokens.append(main)
            for i in range(2, 10):
                t = os.getenv(f"GITHUB_TOKEN_{i}", "")
                if t:
                    tokens.append(t)
            self.github_tokens = tokens

        if not self.gemini_api_key:
            self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")


settings = Settings()

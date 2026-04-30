"""
Centralized configuration for the ElectIQ application.

Provides environment-based configuration with secure defaults
for development, testing, and production environments.
"""

import os
from typing import Final


class Config:
    """Base configuration with secure defaults."""

    # Application
    APP_NAME: Final[str] = "ElectIQ"
    APP_VERSION: Final[str] = "1.0.0"
    APP_DESCRIPTION: Final[str] = "AI-Powered Election Process Education"

    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", os.urandom(32).hex())
    MAX_MESSAGE_LENGTH: Final[int] = 500
    RATE_LIMIT_DEFAULT: Final[str] = "200 per day"
    RATE_LIMIT_CHAT: Final[str] = "15 per minute"

    # Google Gemini AI
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL: Final[str] = "gemini-2.0-flash"
    GEMINI_TEMPERATURE: Final[float] = 0.7
    GEMINI_MAX_TOKENS: Final[int] = 600

    # Server
    PORT: int = int(os.environ.get("PORT", 8080))
    DEBUG: bool = False

    # Cache
    CACHE_TYPE: Final[str] = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT: Final[int] = 30


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration with stricter defaults."""

    DEBUG = False


def get_config() -> Config:
    """Return the appropriate configuration based on FLASK_ENV."""
    env = os.environ.get("FLASK_ENV", "production")
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
    }
    return configs.get(env, ProductionConfig)()

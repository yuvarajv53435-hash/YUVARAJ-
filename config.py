from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_outline_model: str = "gemini-2.5-flash"
    gemini_story_model: str = "gemini-2.5-flash"

    hf_api_key: str = ""
    hf_image_model: str = (
        "stabilityai/stable-diffusion-xl-base-1.0"
    )

    # Supported modes: auto, huggingface, diffusers, placeholder
    image_backend: str = "auto"

    use_local_diffusers: bool = False
    diffusers_model: str = "runwayml/stable-diffusion-v1-5"

    max_panels: int = 5
    request_timeout: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
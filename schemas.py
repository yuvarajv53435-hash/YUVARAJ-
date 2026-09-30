from pydantic import BaseModel, Field, field_validator


class PromptRequest(BaseModel):
    prompt: str = Field(min_length=8, max_length=1200)
    character_name: str = Field(
        default="Alex", min_length=1, max_length=60
    )
    setting: str = Field(
        default="enchanted forest", max_length=120
    )
    tone: str = Field(default="adventurous", max_length=60)
    art_style: str = Field(default="comic book", max_length=80)

    @field_validator(
        "prompt",
        "character_name",
        "setting",
        "tone",
        "art_style",
    )
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value


class ImageTestRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=800)
    art_style: str = Field(default="comic book", max_length=80)
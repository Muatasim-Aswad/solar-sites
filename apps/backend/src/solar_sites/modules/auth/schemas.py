from pydantic import EmailStr, Field, field_validator

from solar_sites.platform.schemas import ApiModel


class Credentials(ApiModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=12, max_length=128, strict=True)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class SessionOutput(ApiModel):
    csrf_token: str


class MeOutput(SessionOutput):
    email: str

import re
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmailRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(min_length=3, max_length=254)

    @field_validator('email')
    @classmethod
    def safe_email(cls, value):
        value = value.strip().casefold()
        if not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.[a-z]{2,63}", value):
            raise ValueError('Enter a valid email address')
        return value


class ConfirmRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    token: str = Field(min_length=20, max_length=256)


class RecoverRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    case_id: UUID
    code: str = Field(min_length=20, max_length=256)


class DeleteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    confirmation: str = Field(pattern='^DELETE$')

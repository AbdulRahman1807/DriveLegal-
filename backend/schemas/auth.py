from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    language_preference: str = Field(default="en", max_length=10)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    language_preference: Optional[str] = Field(None, max_length=10)
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_password_change(self):
        if self.new_password and not self.current_password:
            raise ValueError("current_password is required to set a new password.")
        return self


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    id: UUID
    email: str
    role: str
    language_preference: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

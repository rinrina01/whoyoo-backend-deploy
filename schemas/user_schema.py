from datetime import date
from pydantic import BaseModel

class UserUpdate(BaseModel):
    email:  str | None = None
    sexuality:  str | None = None
    description:  str | None = None

class UserLogin(BaseModel):
    email: str | None = None
    password: str | None = None

class TokenData(BaseModel):
    id: int = None
    email: str = None
    date_of_birth: date = None
    sexuality: str | None = None
    gender: str | None = None
    description: str | None = None
    is_validated: bool = False
from datetime import date
from typing import List

from pydantic import BaseModel, EmailStr

# TODO handle email format errors in frontend

class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email:  EmailStr | None = None
    description:  str | None = None
    interests: List[int] | None = None

class UserLogin(BaseModel):
    email: EmailStr | None = None
    password: str | None = None

class TokenData(BaseModel):
    id: int = None
    email: str = None
    
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    username: str
    birthdate: str
    description: str
    sexuality: str | None = None
    gender: str | None = None
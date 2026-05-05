from datetime import date
from typing import List
from pydantic import BaseModel

class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email:  str | None = None
    description:  str | None = None
    background_image: str | None = None
    photos: List[str] | None = None
    vocals: List[str] | None = None

class UserLogin(BaseModel):
    email: str | None = None
    password: str | None = None

class TokenData(BaseModel):
    id: int = None
    email: str = None
    date_of_birth: str = None
    sexuality: str | None = None
    gender: str | None = None
    description: str | None = None
    is_validated: bool = False
    last_name: str | None = None
    first_name: str | None = None
    background_image: str | None = None
    
class UserSignup(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    username: str
    birthdate: str
    description: str
    sexuality: str | None = None
    gender: str | None = None

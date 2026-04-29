from pydantic import BaseModel

class UserUpdate(BaseModel):
    email:  str | None = None
    sexuality:  str | None = None
    description:  str | None = None

class UserLogin(BaseModel):
    email: str | None = None
    password: str | None = None

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
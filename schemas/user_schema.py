from pydantic import BaseModel

class UserUpdate(BaseModel):
    email:  str | None = None
    sexuality:  str | None = None
    description:  str | None = None

class UserLogin(BaseModel):
    email: str | None = None
    password: str | None = None
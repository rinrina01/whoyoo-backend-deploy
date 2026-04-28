from pydantic import BaseModel

class UserUpdate(BaseModel):
    email:  str | None = None
    sexuality:  str | None = None
    description:  str | None = None
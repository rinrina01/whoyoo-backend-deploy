from sqlmodel import SQLModel, Field
from typing import List, Optional, Dict
from datetime import date, datetime

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(default='')
    password: str = Field()
    name: str = Field(default='')
    date_of_birth: date = Field(default=None)
    sexuality: str | None = Field(default=None)
    gender: str = Field(default=None)
    description: str = Field(default='')
    is_validated: bool = Field(default=False)
    joined_at: datetime = Field(default_factory=datetime.now)

class Swipe(SQLModel, table=True):
    id: int = Field(primary_key=True)
    active_user_id: int = Field(default=None, foreign_key="user.id")
    swiped_user_id: int = Field(default=None, foreign_key="user.id")
    swiped_at: datetime = Field(default_factory=datetime.now)
    status: str


class Conversations(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id1: int = Field(default=None, foreign_key="user.id")
    user_id2: int = Field(default=None, foreign_key="user.id")


class Message(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    conversation_id: int = Field(default=None, foreign_key="conversations.id")
    sender_id: int = Field(default=None, foreign_key="user.id")
    text: str
    sent_at: datetime = Field(default_factory=datetime.now)
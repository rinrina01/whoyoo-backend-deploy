from datetime import date
from pydantic import BaseModel

class MessageCreation(BaseModel):
    chat_id: int = None
    sender_id: int = None
    receiver_id: int = None
    content: str = None
import bcrypt
import jwt
import os

from fastapi import APIRouter, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.dialects.mssql import json

from database import supabase
from schemas.user_schema import TokenData
from schemas.chat_schema import MessageCreation

router = APIRouter(tags=["Chats"])

@router.get("/chats")
def get_chats():
    response = supabase.table("chats").select("*").execute()
    return response.data

@router.get("/chats/{chat_id}")
def get_chat(chat_id: str):
    response = (
        supabase.table("messages")
        .select("*")
        .eq("chat_id", chat_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="No results.")
    return response.data

@router.post("/chats/send-message")
def send_message(request: MessageCreation):
    response = (
        supabase.table("messages")
        .insert({
            "chat_id": request.chat_id,
            "sender_id": request.sender_id,
            "receiver_id": request.receiver_id,
            "content": request.content,
        })
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Message creation failed")

    return response.data
import bcrypt
import jwt
import os

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
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

def create_message(chat_id, sender_id, receiver_id, content):
    return (
        supabase.table("messages")
        .insert({
            "chat_id": chat_id,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content,
        })
        .execute()
    )

"""
@router.post("/chats/send-message")
def send_message(request: MessageCreation):
    response = create_message(
        request.chat_id,
        request.sender_id,
        request.receiver_id,
        request.content
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Message creation failed")

    return response.data
"""

chat_connections = {}  # chat_id -> list of websockets
@router.websocket("/ws/chat/{chat_id}")
async def chat_ws(websocket: WebSocket, chat_id: int):
    await websocket.accept()

    if chat_id not in chat_connections:
        chat_connections[chat_id] = []

    chat_connections[chat_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()

            sender_id = data["sender_id"]
            receiver_id = data["receiver_id"]
            content = data["content"]

            create_message(chat_id, sender_id, receiver_id, content)

            disconnected_clients = []

            for client in chat_connections[chat_id]:
                try:
                    await client.send_json(data)
                except:
                    disconnected_clients.append(client)

            # remove dead sockets
            for client in disconnected_clients:
                chat_connections[chat_id].remove(client)

    except WebSocketDisconnect:
        if websocket in chat_connections[chat_id]:
            chat_connections[chat_id].remove(websocket)
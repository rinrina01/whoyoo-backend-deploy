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

@router.get("/chats/{user_id}")
def get_chats(user_id: str):

    try:
        # Fetch all chats where user is participant
        chats_response = (
            supabase.table("chats")
            .select("*")
            .or_(f"user_1.eq.{user_id},user_2.eq.{user_id}")
            .execute()
        )

        chats = chats_response.data

        if not chats:
            return []

        formatted_chats = []

        for chat in chats:

            # Determine the OTHER participant
            other_user_id = (
                chat["user_2"]
                if str(chat["user_1"]) == str(user_id)
                else chat["user_1"]
            )

            # Fetch other user's info
            user_response = (
                supabase.table("users")
                .select("id, username, background_image")
                .eq("id", other_user_id)
                .single()
                .execute()
            )

            other_user = user_response.data

            # Fetch latest message
            message_response = (
                supabase.table("messages")
                .select("content, created_at, sender_id")
                .eq("chat_id", chat["id"])
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            last_message = (
                message_response.data[0]
                if message_response.data
                else None
            )

            formatted_chats.append({
                "chat_id": chat["id"],

                "user": {
                    "id": other_user["id"],
                    "username": other_user["username"],
                    "background_image": other_user["background_image"],
                },

                "last_message": (
                    last_message["content"]
                    if last_message
                    else None
                ),

                "last_message_date": (
                    last_message["created_at"]
                    if last_message
                    else None
                ),

                "last_message_sender_id": (
                    last_message["sender_id"]
                    if last_message
                    else None
                )
            })

        # Sort chats by latest message date
        formatted_chats.sort(
            key=lambda x: x["last_message_date"] or "",
            reverse=True
        )

        return formatted_chats

    except Exception as e:
        print("CHAT FETCH ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail="Could not fetch chats"
        )

@router.get("/chats/{chat_id}")
def get_chat(chat_id: str):
    response = (
        supabase.table("messages")
        .select("*")
        .eq("chat_id", chat_id)
        .order("created_at", desc=False)  # ✅ important
        .execute()
    )

    if not response.data:
        return []  # don't throw 404 for empty chat

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
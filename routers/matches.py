from fastapi import APIRouter, HTTPException
from database import supabase

router = APIRouter(tags=["Matches"])

@router.post("/matches/{receiver_id}")
def like_user(receiver_id: int, sender_id: int):

    # Vérifier si l'autre a déjà liké
    existing = (
        supabase.table("matches")
        .select("*")
        .eq("sender_id", receiver_id)
        .eq("receiver_id", sender_id)
        .execute()
    )

    if existing.data:
        # L'autre a déjà liké → c'est un MATCH
        supabase.table("matches").update(
            {"is_matched": True}
        ).eq("sender_id", receiver_id).eq("receiver_id", sender_id).execute()

        # Créer le chat
        supabase.table("chats").insert(
            {"user_1": sender_id, "user_2": receiver_id}
        ).execute()

        return {"matched": True}

    # Sinon on enregistre juste le like
    supabase.table("matches").insert({
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "is_matched": False
    }).execute()

    return {"matched": False}
import uuid
import jwt
import os

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
from database import supabase

router = APIRouter(tags=["Profile Items"])

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"


# ─── Helper : décoder le token ──────ddsdqsds──────────────────────────────────────────

def _get_user_id(authorization: str) -> str:
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return str(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ─── GET /users/{user_id}/pinned-items ───────────────────────────────────────

@router.get("/users/{user_id}/pinned-items")
def get_pinned_items(user_id: str):
    """
    Retourne les items pinnés d'un utilisateur (picture + vocal).
    Public — pas d'auth requise, utilisé pour les cartes de découverte.
    """
    response = (
        supabase.table("profile_items")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_pinned", True)
        .execute()
    )

    items = response.data or []
    pinned_picture = next((i for i in items if i["type"] == "picture"), None)
    pinned_vocal   = next((i for i in items if i["type"] == "vocal"),   None)

    return {
        "pinned_picture": pinned_picture,
        "pinned_vocal":   pinned_vocal,
    }


# ─── GET /users/me/items ──────────────────────────────────────────────────────


@router.get("/users/me/items")
def get_my_items(authorization: str = Header(...)):
    """Retourne tous les profile_items (pictures + vocals) de l'utilisateur connecté."""
    user_id = _get_user_id(authorization)

    response = (
        supabase.table("profile_items")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data


# ─── POST /users/{user_id}/upload-picture ────────────────────────────────────

@router.post("/users/{user_id}/upload-picture")
async def upload_picture(
    user_id: str,
    file: UploadFile = File(...),
    caption: str = Form(default=""),
    authorization: str = Header(...),
):
    """Upload une image dans Supabase Storage et crée un profile_item de type 'picture'."""
    token_user_id = _get_user_id(authorization)

    # Sécurité : on ne peut uploader que pour soi-même
    if str(token_user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp", "gif"]:
        raise HTTPException(status_code=400, detail="Format d'image non supporté")

    file_path = f"{user_id}/pictures/{uuid.uuid4()}.{ext}"
    content = await file.read()

    try:
        supabase.storage.from_("user_uploads").upload(
            path=file_path,
            file=content,
            file_options={"content-type": file.content_type},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur storage : {str(e)}")

    public_url = supabase.storage.from_("user_uploads").get_public_url(file_path)

    # Insérer dans profile_items
    try:
        item_response = (
            supabase.table("profile_items")
            .insert({
                "user_id": int(user_id),
                "type": "picture",
                "url": public_url,
                "caption": caption if caption else None,
                "is_pinned": False,
            })
            .execute()
        )
        print("INSERT result:", item_response.data)
        print("INSERT error:", getattr(item_response, 'error', None))
    except Exception as e:
        print("INSERT exception:", str(e))
        raise HTTPException(status_code=500, detail=f"Erreur insert BDD : {str(e)}")

    if not item_response.data:
        raise HTTPException(status_code=500, detail="Insert échoué silencieusement — vérifier les logs")

    return item_response.data[0]


# ─── POST /users/{user_id}/upload-voice ──────────────────────────────────────

@router.post("/users/{user_id}/upload-voice")
async def upload_voice(
    user_id: str,
    file: UploadFile = File(...),
    caption: str = Form(default=""),
    authorization: str = Header(...),
):
    """Upload un fichier audio dans Supabase Storage et crée un profile_item de type 'vocal'."""
    token_user_id = _get_user_id(authorization)

    if str(token_user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    ext = file.filename.split(".")[-1].lower()
    if ext not in ["m4a", "mp3", "wav", "ogg", "aac"]:
        raise HTTPException(status_code=400, detail="Format audio non supporté")

    file_path = f"{user_id}/vocals/{uuid.uuid4()}.{ext}"
    content = await file.read()

    try:
        supabase.storage.from_("user_uploads").upload(
            path=file_path,
            file=content,
            file_options={"content-type": file.content_type or "audio/mp4"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur storage : {str(e)}")

    public_url = supabase.storage.from_("user_uploads").get_public_url(file_path)

    try:
        item_response = (
            supabase.table("profile_items")
            .insert({
                "user_id": int(user_id),
                "type": "vocal",
                "url": public_url,
                "caption": caption if caption else None,
                "is_pinned": False,
            })
            .execute()
        )
        print("INSERT result:", item_response.data)
        print("INSERT error:", getattr(item_response, 'error', None))
    except Exception as e:
        print("INSERT exception:", str(e))
        raise HTTPException(status_code=500, detail=f"Erreur insert BDD : {str(e)}")

    if not item_response.data:
        raise HTTPException(status_code=500, detail="Insert échoué silencieusement — vérifier les logs")

    return item_response.data[0]


# ─── POST /items/{item_id}/toggle-pin ────────────────────────────────────────

@router.post("/items/{item_id}/toggle-pin")
def toggle_pin(item_id: str, authorization: str = Header(...)):
    """
    Bascule is_pinned d'un item.
    Si on pin un item, tous les autres items du même type sont dépinés (1 seul pin par type).
    """
    user_id = _get_user_id(authorization)

    # Récupérer l'item
    item_resp = (
        supabase.table("profile_items")
        .select("*")
        .eq("id", item_id)
        .single()
        .execute()
    )

    if not item_resp.data:
        raise HTTPException(status_code=404, detail="Item not found")

    item = item_resp.data

    # Vérifier que l'item appartient à l'utilisateur
    if str(item["user_id"]) != str(user_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    new_pinned = not item["is_pinned"]

    # Si on pin → dépiner tous les autres items du même type d'abord
    if new_pinned:
        supabase.table("profile_items").update({"is_pinned": False}).eq(
            "user_id", item["user_id"]
        ).eq("type", item["type"]).execute()

    # Mettre à jour l'item cible
    updated = (
        supabase.table("profile_items")
        .update({"is_pinned": new_pinned})
        .eq("id", item_id)
        .execute()
    )

    return updated.data[0]


# ─── DELETE /items/{item_id} ──────────────────────────────────────────────────

@router.delete("/items/{item_id}")
def delete_item(item_id: str, authorization: str = Header(...)):
    """Supprime un profile_item (et son fichier dans le storage)."""
    user_id = _get_user_id(authorization)

    item_resp = (
        supabase.table("profile_items")
        .select("*")
        .eq("id", item_id)
        .single()
        .execute()
    )

    if not item_resp.data:
        raise HTTPException(status_code=404, detail="Item not found")

    item = item_resp.data

    if str(item["user_id"]) != str(user_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Extraire le path relatif depuis l'URL publique pour supprimer du storage
    # URL format: .../storage/v1/object/public/user_uploads/{path}
    try:
        url: str = item["url"]
        storage_path = url.split("/user_uploads/")[-1]
        supabase.storage.from_("user_uploads").remove([storage_path])
    except Exception:
        pass  # On supprime l'entrée BDD même si le fichier storage échoue

    supabase.table("profile_items").delete().eq("id", item_id).execute()

    return {"deleted": True, "id": item_id}

import uuid

import bcrypt
import jwt
import os

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database import supabase
from schemas.user_schema import *
from datetime import datetime, timedelta

router = APIRouter(tags=["Users"])

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
BEARER_SCHEME = HTTPBearer()

# *--------- UTILITY FUNCTIONS ---------- #

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def generate_token(user: TokenData) -> str:
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(hours=24), # TODO change
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_user(authorization: HTTPAuthorizationCredentials = Depends(BEARER_SCHEME)):
    try:
        return jwt.decode(authorization.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def authenticate_user(email: str, password: str):
    try:
        response = (
            supabase.table("users")
            .select("id, email, password")
            .eq("email", email)
            .execute()
        )
    except Exception as e:
        print("Supabase error:", e)
        raise HTTPException(status_code=500, detail="Database error")
    if not response.data:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user = response.data[0]
    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user

# *--------- ROUTES ---------- #
# --------- AUTH --------- #

@router.post("/users/signup")
def signup_user(request: UserSignup):
    hashed_password = get_password_hash(request.password)
    email = request.email.lower().strip()
    username = request.username.strip()
    try:
        response = (
            supabase.table("users")
            .insert({
                "email": email,
                "password": hashed_password,
                "first_name": request.first_name,
                "last_name": request.last_name,
                "username": username,
                "birthdate": request.birthdate,
                "description": request.description,
                "sexuality": request.sexuality,
                "gender": request.gender,
            })
            .execute()
        )
    except Exception as e:
        error_str = str(e)
        if "unique_email" in error_str:
            raise HTTPException(
                status_code=409,
                detail="Email already in use"
            )
        if "unique_username" in error_str:
            raise HTTPException(
                status_code=409,
                detail="Username already taken"
            )
        print("Supabase error:", e)
        raise HTTPException(status_code=500, detail="Database error")
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not create user")

    user = response.data[0]
    token_data = TokenData(
        id=user['id'],
        email=user['email'],
    )
    return {"token": generate_token(token_data)}

@router.post("/users/login")
def login_user(request: UserLogin):
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token_data = TokenData(
        id=user['id'],
        email=user['email'],
    )
    return {"token": generate_token(token_data)}

@router.put("/users/modify/{user_id}")
def modify_user(user_id: str, user: UserUpdate):
    update_data = user.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:                                         # ← ajout
        response = (
            supabase.table("users")
            .update(update_data)
            .eq("id", user_id)
            .execute()
        )
    except Exception:                            # ← ajout
        raise HTTPException(
            status_code=500,
            detail="Database connection error"
        )

    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")

    return response.data


# --------- OTHER --------- #

@router.get("/users/me")
def get_me(
    authorization: HTTPAuthorizationCredentials = Depends(BEARER_SCHEME)
):
    try:
        payload = jwt.decode(
            authorization.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        try:
            response = (
                supabase.table("users")
                .select(
                    """
                        id,
                        email,
                        first_name,
                        last_name,
                        username,
                        birthdate,
                        description,
                        created_at,
                        gender,
                        sexuality,
                        is_verified,
                        background_image,
                        interests,
                        playlist,
                        pictures,
                        vocals
                    """
                )
                .eq("id", payload["sub"])
                .execute()
            )
        except Exception as e:
            print("Supabase error:", e)
            raise HTTPException(status_code=500, detail="Database error")

        user = response.data[0]
        if not user:
            raise HTTPException(status_code=401, detail="No user was found")
        # return payload
        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/users")
def get_users():
    response = supabase.table("users").select("*").execute()
    return response.data

@router.get("/users/{user_id}")
def get_user(user_id: str):
    response = (
        supabase.table("users")
        .select("*")
        .eq("id", user_id)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="No results.")
    return response.data

@router.post("/users/me/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    authorization: str = Header(...),  # ← Header direct
):
    # Extraire le token manuellement
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload["sub"]
    ext = file.filename.split(".")[-1]
    file_path = f"{user_id}/{uuid.uuid4()}.{ext}"

    content = await file.read()

    supabase.storage.from_("user_uploads").upload(
        path=file_path,
        file=content,
        file_options={"content-type": file.content_type},
    token_data = TokenData(
        id=user.get('id'),
        email=user['email'],
        date_of_birth=str(user['birthdate']),
        sexuality=user['sexuality'],
        gender=user['gender'],
        description=user['description'],
        first_name=user['first_name'],
        last_name=user['last_name'],
        background_image=user.get('background_image'),
    )
    public_url = supabase.storage.from_("user_uploads").get_public_url(file_path)

    supabase.table("users").update(
        {"background_image": public_url}
    ).eq("id", user_id).execute()

    return {"background_image": public_url}

@router.post("/users/{user_id}/upload-picture")
async def upload_picture(
        user_id: str,
        file: UploadFile = File(...)
):

    try:
        file_bytes = await file.read()


        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{user_id}/{uuid.uuid4()}.{file_extension}"


        supabase.storage.from_("user_uploads").upload(
            path=unique_filename,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )

        public_url = supabase.storage.from_("user_uploads").get_public_url(unique_filename)


        user_response = supabase.table("users").select("pictures").eq("id", user_id).single().execute()
        current_pictures = user_response.data.get("pictures", []) if user_response.data else []

        if current_pictures is None:
            current_pictures = []

        current_pictures.append(public_url)


        supabase.table("users").update({"pictures": current_pictures}).eq("id", user_id).execute()

        return {
            "message": "Upload successful",
            "url": public_url
        }

    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/upload-voice")
async def upload_voice(
        user_id: str,
        file: UploadFile = File(...)
):

    try:
        file_bytes = await file.read()


        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{user_id}/{uuid.uuid4()}.{file_extension}"


        supabase.storage.from_("user_uploads").upload(
            path=unique_filename,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )


        public_url = supabase.storage.from_("user_uploads").get_public_url(unique_filename)


        user_response = supabase.table("users").select("vocals").eq("id", user_id).single().execute()
        current_vocals = user_response.data.get("vocals", []) if user_response.data else []

        if current_vocals is None:
            current_vocals = []

        current_vocals.append(public_url)

        supabase.table("users").update({"vocals": current_vocals}).eq("id", user_id).execute()

        return {
            "message": "Voice upload successful",
            "url": public_url
        }

    except Exception as e:
        print(f"Voice upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
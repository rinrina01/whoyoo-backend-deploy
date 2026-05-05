import bcrypt
import jwt
import os

from fastapi import APIRouter, HTTPException, Depends
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
        "exp": datetime.utcnow() + timedelta(hours=24),
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
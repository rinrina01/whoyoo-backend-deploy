import bcrypt
import jwt
import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer
from sqlalchemy.dialects.mssql import json

from database import supabase
from schemas.user_schema import UserUpdate, UserLogin, TokenData, UserSignup

router = APIRouter(tags=["Users"])

secret_key = os.environ.get("SECRET_KEY")
algorithm = "HS256"
bearer_scheme = HTTPBearer()

def generate_token(user: TokenData) -> str:
    return jwt.encode(user.model_dump(), secret_key, algorithm=algorithm)

'''
def populate_users():
    users = [
        User(
            name="Ascot Brick",
            password="hashed_password_1",
            date_of_birth=date(1995, 6, 15),
            sexuality="straight",
            gender="male",
            description="Loves architecture and vintage design."
        ),
        User(
            name="Luna Hayes",
            password="hashed_password_2",
            date_of_birth=date(1998, 11, 3),
            sexuality="bisexual",
            gender="female",
            description="Book lover and night owl."
        ),
        User(
            name="Kai Moreno",
            password="hashed_password_3",
            date_of_birth=date(2000, 2, 21),
            sexuality="pansexual",
            gender="non-binary",
            description="Coffee addict and digital artist."
        ),
    ]

    with Session(database.engine) as session:
        existing_count = session.exec(select(User)).first()
        if existing_count:
            print("User table already populated. Skipping insertion.")
            return
        else :
            for user in users:
                session.add(user)
                print("Added " + str(user.name) + " to userbase.")
        session.commit()
        print("User table populated successfully.")
'''

# *--------- ROUTES ----------#

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
    response = (
        supabase.table("users")
        .select("*")
        .eq("email", request.email)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")

    user = response.data
    print(user)
    # Check if the password are the same
    if not bcrypt.checkpw(request.password.encode("utf-8"), user['password'].encode("utf-8")):
        raise HTTPException(status_code=404, detail="Incorrect password")

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
    return {"token": generate_token(token_data)}

@router.post("/users/signup")
def signup_user(request: UserSignup):
    hashed_password = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    response = (
        supabase.table("users")
        .insert({
            "email": request.email,
            "password": hashed_password,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "username": request.username,
            "birthdate": request.birthdate,
            "description": request.description,
            "sexuality": request.sexuality,
            "gender": request.gender,
        })
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Could not create user")

    new_user = response.data[0]
    token_data = TokenData(
        id=new_user.get('id'),
        email=new_user['email'],
        date_of_birth=str(new_user['birthdate']),
        sexuality=new_user['sexuality'],
        gender=new_user['gender'],
        description=new_user['description'],
    )

    return {"token": generate_token(token_data)}


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
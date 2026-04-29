import bcrypt
import jwt
import os
from fastapi import APIRouter, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.dialects.mssql import json

from database import supabase
from schemas.user_schema import UserUpdate, UserLogin, TokenData

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
    update_data = user.model_dump()

    response = (
        supabase.table("users")
        .update(update_data)
        .eq("id", user_id)
        .execute()
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
        #Delete the row below when we have hashed password
        .eq("password", request.password)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")

    user = response.data

    # #Check if the password are the same
    # if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
    #     raise HTTPException(status_code=404, detail="Incorrect password")

    token_data = TokenData(id=user.id, email=user.email, date_of_birth=user.date_of_birth, sexuality=user.sexuality, gender=user.gender, description=user.description)
    return {"token": generate_token(token_data)}
@router.post("/users/signup")
def signup_user(request: UserLogin):
    response = (
        supabase.table("users")
        .insert({
            "email": request.email,
            "password": request.password,
        })
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Could not create user")

    return response.data
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from models import User
from datetime import date, datetime
import database

router = APIRouter(tags=["Users"])

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

# *--------- ROUTES ----------#

@router.get("/users")
def get_users(session: Session = Depends(database.get_session)):
    statement = select(User)
    users = session.exec(statement).all()

    return {
        "users": [
            {
                "id": user.id,
                "name": user.name,
            }
            for user in users
        ],
    }

@router.get("/users/{user_id}")
def get_user(user_id: int, session: Session = Depends(database.get_session)):
    statement = (
        select(User)
        .where(User.id == user_id)
    )
    user = session.exec(statement).all()

    if not user:
        raise HTTPException(status_code=404, detail="No results.")
    return user
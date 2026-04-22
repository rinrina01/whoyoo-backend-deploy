from fastapi import APIRouter, HTTPException
from database import supabase

router = APIRouter(tags=["Users"])

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
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="No results.")

    return response.data
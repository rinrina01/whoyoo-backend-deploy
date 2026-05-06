from fastapi import APIRouter, HTTPException
from database import supabase

router = APIRouter(tags=["Interests"])


@router.get("/interests")
def get_all_interests():
    response = supabase.table("interests").select("*").execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="No interests found")
    return response.data


@router.get("/interests/resolve")
def resolve_interests(ids: str):
    """ids = comma-separated list of ints, ex: ?ids=1,3,5"""
    try:
        id_list = [int(i) for i in ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ids format")

    response = (
        supabase.table("interests")
        .select("*")
        .in_("id", id_list)
        .execute()
    )
    return response.data
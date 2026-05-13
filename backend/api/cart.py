from fastapi import APIRouter, Depends
from db.database import get_db
from agent.tools.cart import get_cart

router = APIRouter()


@router.get("/cart/{session_id}")
async def get_cart_endpoint(session_id: str, db=Depends(get_db)):
    return await get_cart(session_id=session_id, db=db)

from fastapi import APIRouter, HTTPException
import uuid
from tokens import create_access_token

router = APIRouter(
    prefix="/auth/",
    tags=["Auth"]
)

@router.post("/login")
async def login(username: str, password: str):
    if username and password:
        user_id = str(uuid.uuid4())
        access_token = create_access_token(data={
            "sub" : user_id,
            "username" : username
        })
        return {
            "access_token" : access_token,
            "token_type" : "bearer",
            "user_id" : user_id,
            "username" : username
        }
    raise HTTPException(status_code=401, detail="Invalid Credentials")



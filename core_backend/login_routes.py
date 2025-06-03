from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
from tokens import create_access_token, get_current_user
from pydantic import BaseModel

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

security = HTTPBearer()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    username: str

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # Simple validation - replace with proper authentication
    if request.username and request.password:
        user_id = str(uuid.uuid4())
        access_token = create_access_token(data={
            "sub": user_id,
            "username": request.username
        })
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id,
            username=request.username
        )
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return current_user

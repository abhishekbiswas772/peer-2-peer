from dataclasses import asdict
import json
from fastapi import APIRouter, Depends, WebSocket
from fastapi.exceptions import HTTPException
from tokens import get_current_user
import uuid
from models import Room
from datetime import datetime
from connetion_manager import ConnectionManager
from configs import Config


router = APIRouter(
    prefix="/messaging/",
    tags=["Chats"]
)

manager = ConnectionManager()

@router.post("/room")
async def create_room(
    name : str,
    max_participants : int  = 10,
    current_user : str = Depends(get_current_user)
):
    room_id = str(uuid.uuid4())
    room = Room(
        id=room_id,
        name=name,
        created_by = current_user,
        created_at=datetime.now(),
        max_participants=max_participants
    )
    if manager.redis_client:
        await manager.redis_client.set(f"room:{room_id}", json.dumps(asdict(room), default=str))

    return room


@router.get("/rooms/{room_id}")
async def get_room(room_id : str, current_user: str = Depends(get_current_user)):
    if manager.redis_client:
        room_data = await manager.redis_client.get(f"room:{room_id}")
        if room_data:
            return json.loads(room_data)
        
    return HTTPException(status_code=404, detail="Room not Found")


@router.get("/ice-servers")
async def get_ice_server():
    return {
        "iceServers" : Config.stun_servers + Config.turn_servers
    }
    

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str):
    pass
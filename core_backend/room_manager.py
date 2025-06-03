from dataclasses import asdict
import json
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from tokens import get_current_user
import uuid
from models import Room
from datetime import datetime
from connection_manager import manager
from configs import Config
from jose import jwt, JWTError
from websocket_handler import handle_websocket_message
from pydantic import BaseModel
import os
import aiofiles
from typing import List

router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"]
)

class CreateRoomRequest(BaseModel):
    name: str
    max_participants: int = 10
    password: str = None
    is_public: bool = True

@router.post("/")
async def create_room(
    request: CreateRoomRequest,
    current_user: dict = Depends(get_current_user)
):
    room_id = str(uuid.uuid4())
    room = Room(
        id=room_id,
        name=request.name,
        created_by=current_user["user_id"],
        created_at=datetime.now(),
        max_participants=request.max_participants,
        password=request.password,
        is_public=request.is_public
    )
    
    if manager.redis_client:
        try:
            await manager.redis_client.set(
                f"room:{room_id}", 
                json.dumps(asdict(room), default=str)
            )
        except Exception as e:
            print(f"Redis error: {e}")

    return room

@router.get("/{room_id}")
async def get_room(room_id: str, current_user: dict = Depends(get_current_user)):
    if manager.redis_client:
        try:
            room_data = await manager.redis_client.get(f"room:{room_id}")
            if room_data:
                room_info = json.loads(room_data)
                # Add current participants
                room_info["current_participants"] = manager.get_room_participants(room_id)
                room_info["participant_count"] = len(room_info["current_participants"])
                return room_info
        except Exception as e:
            print(f"Redis error: {e}")
    
    raise HTTPException(status_code=404, detail="Room not found")

@router.get("/")
async def list_public_rooms(current_user: dict = Depends(get_current_user)):
    # This would require a proper database in production
    return {"message": "Public rooms listing - implement with proper database"}

@router.get("/{room_id}/ice-servers")
async def get_ice_servers():
    return {
        "iceServers": Config.stun_servers + Config.turn_servers
    }

@router.get("/{room_id}/messages")
async def get_chat_history(
    room_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    if manager.redis_client:
        try:
            messages = await manager.redis_client.lrange(f"chat:{room_id}", 0, limit - 1)
            decrypted_messages = []

            for msg in messages:
                try:
                    message_data = json.loads(msg)
                    if "content" in message_data:
                        message_data["content"] = manager.decrypt_message(message_data["content"])
                    decrypted_messages.append(message_data)
                except Exception as e:
                    print(f"Error decrypting message: {e}")
                    continue
            
            return {"messages": list(reversed(decrypted_messages))}
        except Exception as e:
            print(f"Redis error: {e}")
    
    return {"messages": []}

@router.get("/{room_id}/whiteboard")
async def get_whiteboard_state(
    room_id: str,
    current_user: dict = Depends(get_current_user)
):
    if manager.redis_client:
        try:
            events = await manager.redis_client.lrange(f"whiteboard:{room_id}", 0, -1)
            whiteboard_events = [json.loads(event) for event in events]
            return {"events": list(reversed(whiteboard_events))}
        except Exception as e:
            print(f"Redis error: {e}")
    
    return {"events": []}

@router.post("/{room_id}/upload")
async def upload_file(
    room_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # Check file size
    if file.size > Config.max_file_size:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Create upload directory if it doesn't exist
    upload_dir = f"{Config.upload_directory}/{room_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = f"{upload_dir}/{file.filename}"
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Broadcast file share message
    file_info = {
        "filename": file.filename,
        "file_size": file.size,
        "file_type": file.content_type,
        "uploaded_by": current_user["username"],
        "download_url": f"/rooms/{room_id}/download/{file.filename}"
    }
    
    await manager.broadcast_to_room(room_id, {
        "type": "file_shared",
        "file_info": file_info,
        "timestamp": datetime.now().isoformat()
    })
    
    return {"message": "File uploaded successfully", "file_info": file_info}

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str):
    try:
        # Validate token
        payload = jwt.decode(token, Config.secret_key, algorithms=[Config.algorithm])
        user_id = payload.get("sub")
        username = payload.get("username")
        
        if not user_id or not username:
            await websocket.close(code=1008, reason="Invalid token")
            return
            
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        return

    await websocket.accept()
    success = await manager.add_participant(room_id, user_id, username, websocket)
    if not success:
        return

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await handle_websocket_message(room_id, user_id, message)

    except WebSocketDisconnect:
        await manager.remove_participant(user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.remove_participant(user_id)
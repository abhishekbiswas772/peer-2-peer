from data_models import Participant
from models import * 
import redis.asyncio as redis
from typing import Dict, Optional
from cryptography.fernet import Fernet
from configs import Config
from fastapi import WebSocket
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Dict[str, Participant]] = {}
        self.user_rooms: Dict[str, str] = {}  # user_id -> room_id
        self.redis_client: Optional[redis.Redis] = None
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.config = Config()

    async def connect_redis(self):
        try:
            self.redis_client = redis.from_url(self.config.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    async def disconnect_redis(self):
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")

    def encrypt_message(self, message: str) -> str:
        return self.cipher_suite.encrypt(message.encode()).decode()

    def decrypt_message(self, encrypted_message: str) -> str:
        try:
            return self.cipher_suite.decrypt(encrypted_message.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt message: {e}")
            return encrypted_message

    async def remove_participant(self, user_id: str):
        room_id = self.user_rooms.get(user_id)
        if room_id and room_id in self.rooms and user_id in self.rooms[room_id]:
            participant = self.rooms[room_id][user_id]
            username = participant.username
            del self.rooms[room_id][user_id]
            del self.user_rooms[user_id]

            if not self.rooms[room_id]:
                del self.rooms[room_id]
            else:
                await self.broadcast_to_room(room_id, {
                    "type": "user_left",
                    "user_id": user_id,
                    "username": username,
                    "timestamp": datetime.now().isoformat()
                })
            
            logger.info(f"Participant {username} ({user_id}) removed from room {room_id}")

    async def broadcast_to_room(self, room_id: str, message: dict, exclude_user: str = None):
        if room_id not in self.rooms:
            return 

        message_str = json.dumps(message)
        disconnected_users = []
        
        for user_id, participant in self.rooms[room_id].items():
            if exclude_user and user_id == exclude_user:
                continue

            try:
                await participant.websocket.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                disconnected_users.append(user_id)

        for user_id in disconnected_users:
            await self.remove_participant(user_id)

    async def send_to_user(self, room_id: str, user_id: str, message: dict):
        if room_id in self.rooms and user_id in self.rooms[room_id]:
            try:
                await self.rooms[room_id][user_id].websocket.send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                await self.remove_participant(user_id)
        return False 

    async def add_participant(self, room_id: str, user_id: str, username: str, websocket: WebSocket):
        if room_id not in self.rooms:
            self.rooms[room_id] = {}

        if len(self.rooms[room_id]) >= 10:  # Default max participants
            await websocket.close(code=1000, reason="Room is full")
            return False

        participant = Participant(
            user_id=user_id,
            username=username,
            websocket=websocket,
            joined_at=datetime.now()
        )

        self.rooms[room_id][user_id] = participant
        self.user_rooms[user_id] = room_id

        await self.broadcast_to_room(room_id, {
            "type": "user_joined",
            "user_id": user_id,
            "username": username,
            "timestamp": datetime.now().isoformat()
        }, exclude_user=user_id)

        participants = [
            {
                "user_id": p.user_id,
                "username": p.username,
                "video_quality": p.video_quality,
                "is_screen_sharing": p.is_screen_sharing,
                "is_audio_muted": p.is_audio_muted,
                "is_video_muted": p.is_video_muted
            }
            for p in self.rooms[room_id].values()
        ]

        await websocket.send_text(json.dumps({
            "type": "participants_list",
            "participants": participants
        }))
        
        logger.info(f"Participant {username} ({user_id}) added to room {room_id}")
        return True

    def get_room_participants(self, room_id: str):
        if room_id in self.rooms:
            return [
                {
                    "user_id": p.user_id,
                    "username": p.username,
                    "joined_at": p.joined_at.isoformat(),
                    "is_screen_sharing": p.is_screen_sharing,
                    "video_quality": p.video_quality
                }
                for p in self.rooms[room_id].values()
            ]
        return []

manager = ConnectionManager()
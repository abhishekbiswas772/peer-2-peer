from datetime import datetime
from connection_manager import manager
import uuid
import json
import logging

logger = logging.getLogger(__name__)

async def handle_websocket_message(room_id: str, user_id: str, message: dict):
    message_type = message.get("type")
    
    try:
        if message_type == "webrtc_signal":
            await forward_webrtc_signal(room_id, user_id, message)
        elif message_type == "chat_message":
            await handle_chat_message(room_id, user_id, message)
        elif message_type == "whiteboard_event":
            await handle_whiteboard_event(room_id, user_id, message)
        elif message_type == "file_share":
            await handle_file_share(room_id, user_id, message)
        elif message_type == "video_quality_change":
            await handle_video_quality_change(room_id, user_id, message)
        elif message_type == "screen_share":
            await handle_screen_share(room_id, user_id, message)
        elif message_type == "audio_mute":
            await handle_audio_mute(room_id, user_id, message)
        elif message_type == "video_mute":
            await handle_video_mute(room_id, user_id, message)
        else:
            logger.warning(f"Unknown message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling message type {message_type}: {e}")

async def forward_webrtc_signal(room_id: str, from_user: str, message: dict):
    signal_data = message.get("data", {})
    to_user = message.get("to_user")
    
    webrtc_message = {
        "type": "webrtc_signal",
        "signal_type": signal_data.get("type"),
        "data": signal_data,
        "from_user": from_user,
        "timestamp": datetime.now().isoformat()
    }
    
    if to_user:
        await manager.send_to_user(room_id, to_user, webrtc_message)
    else:
        await manager.broadcast_to_room(room_id, webrtc_message, exclude_user=from_user)

async def handle_chat_message(room_id: str, user_id: str, message: dict):
    content = message.get("content", "")
    if not content.strip():
        return
        
    # Get username
    username = "Unknown"
    if room_id in manager.rooms and user_id in manager.rooms[room_id]:
        username = manager.rooms[room_id][user_id].username
    
    encrypted_content = manager.encrypt_message(content)
    
    chat_message = {
        "type": "chat_message",
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "username": username,
        "content": encrypted_content,
        "timestamp": datetime.now().isoformat()
    }
    
    # Store in Redis
    if manager.redis_client:
        try:
            await manager.redis_client.lpush(
                f"chat:{room_id}",
                json.dumps(chat_message)
            )
            await manager.redis_client.ltrim(f"chat:{room_id}", 0, 99)
        except Exception as e:
            logger.error(f"Redis error storing chat message: {e}")

    # Broadcast to room
    # Decrypt for broadcast (since we encrypt for storage)
    broadcast_message = chat_message.copy()
    broadcast_message["content"] = content
    await manager.broadcast_to_room(room_id, broadcast_message)

async def handle_whiteboard_event(room_id: str, user_id: str, message: dict):
    event_data = message.get("data", {})
    event_type = message.get("event_type", "draw")
    
    whiteboard_event = {
        "type": "whiteboard_event",
        "event_type": event_type,
        "user_id": user_id,
        "data": event_data,
        "timestamp": datetime.now().isoformat()
    }
    
    # Store in Redis
    if manager.redis_client:
        try:
            await manager.redis_client.lpush(
                f"whiteboard:{room_id}",
                json.dumps(whiteboard_event)
            )
            await manager.redis_client.ltrim(f"whiteboard:{room_id}", 0, 999)
        except Exception as e:
            logger.error(f"Redis error storing whiteboard event: {e}")

    await manager.broadcast_to_room(room_id, whiteboard_event, exclude_user=user_id)

async def handle_file_share(room_id: str, user_id: str, message: dict):
    file_info = message.get("file_info", {})
    
    file_share_message = {
        "type": "file_share",
        "user_id": user_id,
        "file_info": file_info,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast_to_room(room_id, file_share_message)

async def handle_video_quality_change(room_id: str, user_id: str, message: dict):
    quality = message.get("quality", "medium")
    
    if room_id in manager.rooms and user_id in manager.rooms[room_id]:
        manager.rooms[room_id][user_id].video_quality = quality
    
    quality_message = {
        "type": "video_quality_changed",
        "user_id": user_id,
        "quality": quality,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast_to_room(room_id, quality_message)

async def handle_screen_share(room_id: str, user_id: str, message: dict):
    is_sharing = message.get("is_sharing", False)
    
    if room_id in manager.rooms and user_id in manager.rooms[room_id]:
        manager.rooms[room_id][user_id].is_screen_sharing = is_sharing

    screen_share_message = {
        "type": "screen_share_status",
        "user_id": user_id,
        "is_sharing": is_sharing,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast_to_room(room_id, screen_share_message)

async def handle_audio_mute(room_id: str, user_id: str, message: dict):
    is_muted = message.get("is_muted", False)
    
    if room_id in manager.rooms and user_id in manager.rooms[room_id]:
        manager.rooms[room_id][user_id].is_audio_muted = is_muted

    mute_message = {
        "type": "audio_mute_status",
        "user_id": user_id,
        "is_muted": is_muted,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast_to_room(room_id, mute_message)

async def handle_video_mute(room_id: str, user_id: str, message: dict):
    is_muted = message.get("is_muted", False)
    
    if room_id in manager.rooms and user_id in manager.rooms[room_id]:
        manager.rooms[room_id][user_id].is_video_muted = is_muted

    mute_message = {
        "type": "video_mute_status",
        "user_id": user_id,
        "is_muted": is_muted,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast_to_room(room_id, mute_message)

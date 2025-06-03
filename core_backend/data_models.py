from dataclasses import dataclass
from fastapi import WebSocket
from datetime import datetime
from typing import Optional

@dataclass
class Participant:
    user_id: str
    username: str
    websocket: WebSocket
    joined_at: datetime
    is_screen_sharing: bool = False
    video_quality: str = "medium"
    is_audio_muted: bool = False
    is_video_muted: bool = False
    role: str = "participant"
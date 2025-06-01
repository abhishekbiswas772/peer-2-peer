from dataclasses import dataclass
from fastapi import WebSocket
from datetime import datetime


@dataclass
class Participant:
    user_id : str
    username : str
    websocket : WebSocket
    joined_at : datetime
    is_screen_sharing : bool = False
    video_quality : str = "medium"


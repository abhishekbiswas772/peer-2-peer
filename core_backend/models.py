from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict

class User(BaseModel):
    id : str 
    username : str
    email : str 


class Room(BaseModel):
    id : str
    name : str 
    created_by : str 
    created_at : datetime
    max_participants : int = 10
    is_active : bool = True 

class Message(BaseModel):
    id : str 
    room_id : str 
    user_id : str 
    content : str 
    timestamp : datetime
    message_type : str = "text"

class WebRTCSignal(BaseModel):
    type: str  # offer, answer, ice-candidate
    data: Dict[str, Any]
    from_user: str
    to_user: str
    room_id: str

class WhiteboardEvent(BaseModel):
    room_id : str
    user_id : str
    event_type : str
    data : Dict[Any, Any]
    timestamp : datetime

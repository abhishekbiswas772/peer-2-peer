import os
from typing import List, Dict

class Config:
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_exp_mins: int = 30
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # File upload settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_directory: str = "uploads"
    
    stun_servers = [
        "stun:stun.l.google.com:19302",
        "stun:stun1.l.google.com:19302",
        "stun:stun2.l.google.com:19302"
    ] 

    turn_servers = [
        {
            "urls": "turn:your-turn-server:3478",
            "username": "turnuser",
            "credential": "turnpass"
        }
    ]

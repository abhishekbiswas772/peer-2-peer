


class Config:
    secret_key : str = ""
    algorithm : str = ""
    access_token_exp_mins : int = 30
    redis_url : str = ""

    stun_servers = [
        "stun:stun.l.google.com:19302",
        "stun:stun1.l.google.com:19302"
    ] 

    turn_servers = [
        {
            "urls": "turn:your-turn-server:3478",
            "username": "turnuser",
            "credential": "turnpass"
        }
    ]






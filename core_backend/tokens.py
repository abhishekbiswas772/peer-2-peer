from jose import jwt, JWTError
from datetime import datetime, timedelta
from configs import Config
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 

config = Config()


def create_access_token(data: dict):
    to_encode  = data.copy()
    expire = datetime.now() + timedelta(minutes=config.access_token_exp_mins)
    to_encode.update({
        "exp" : expire
    })
    return jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(create_access_token)):
    try:
        payload = jwt.decode(credentials.credentials, config.secret_key, algorithms=[config.algorithm])
        user_id : str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid Token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")
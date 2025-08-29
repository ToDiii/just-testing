import os
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = os.environ.get("API_KEY")
API_KEY_NAME = "X-API-KEY"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if not API_KEY:
        # If no API_KEY is set in the environment, disable authentication
        return

    if not api_key:
        raise HTTPException(status_code=403, detail="API key is missing")

    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key

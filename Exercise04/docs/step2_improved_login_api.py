"""
Simulated Step 2 output for prompt:
Add input validation, password hashing (bcrypt), and error handling
"""

import bcrypt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

USERS = {
    "admin": bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
}


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


@app.post("/login")
def login(payload: LoginRequest):
    try:
        password_hash = USERS.get(payload.username)
        if not password_hash:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        is_valid = bcrypt.checkpw(
            payload.password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        return {"message": "Login successful"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc

"""
Simulated Step 1 output for prompt:
Create a login API with username and password
"""

from fastapi import FastAPI, HTTPException

app = FastAPI()

# Insecure plaintext credential store
USERS = {
    "admin": "admin123",
    "user1": "password",
}


@app.post("/login")
def login(username: str, password: str):
    if username not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    if USERS[username] != password:
        raise HTTPException(status_code=401, detail="Wrong password")
    return {"message": "Login successful", "user": username}

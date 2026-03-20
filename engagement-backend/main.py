from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import redis
import json
import os

app = FastAPI(title="Engagement System API")

# Add CORS middleware for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
db_path = os.path.join('/data/sqlite', 'engagement.db')

class UserCreate(BaseModel):
    username: str
    email: str
    bio: str = ""

def get_db_connection():
    if not os.path.exists(db_path):
        raise HTTPException(status_code=500, detail="Database not initialized. Please run init_db.py first.")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.post("/users")
def create_user(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (username, email, bio) VALUES (?, ?, ?)',
            (user.username, user.email, user.bio)
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    conn.close()
    return {"id": user_id, "message": "User created successfully"}

@app.get("/users")
def get_users():
    cache_key = "users:all"
    cached_users = redis_client.get(cache_key)
    
    if cached_users:
        print("[CACHE HIT] All Users")
        return json.loads(cached_users)
        
    print("[CACHE MISS] Fetching All Users from DB")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, bio FROM users')
    rows = cursor.fetchall()
    conn.close()
    
    users = [dict(row) for row in rows]
    redis_client.setex(cache_key, 60, json.dumps(users))
    return users

@app.get("/users/{user_id}")
def get_user(user_id: int):
    cache_key = f"user:profile:{user_id}"
    
    # Try Cache First
    cached_profile = redis_client.get(cache_key)
    if cached_profile:
        print(f"[CACHE HIT] User {user_id}")
        return json.loads(cached_profile)
    
    print(f"[CACHE MISS] User {user_id} - Fetching from DB")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, bio FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        profile = dict(row)
        # Store in Cache with 1 hour TTL
        redis_client.setex(cache_key, 3600, json.dumps(profile))
        return profile
    
    raise HTTPException(status_code=404, detail="User not found")

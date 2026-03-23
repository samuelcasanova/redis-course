from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
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


class EngagementRequest(BaseModel):
    user_id: int


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


@app.get("/users/top")
def get_top_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.id, u.username, u.email, u.bio, COUNT(p.id) as post_count
        FROM users u
        LEFT JOIN posts p ON u.id = p.user_id
        GROUP BY u.id
        ORDER BY post_count DESC LIMIT 3
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


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


@app.get("/posts/recent")
def get_recent_posts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.title, p.text, p.timestamp, p.likes, p.views,
               u.id as author_id, u.username as author_username
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.timestamp DESC LIMIT 6
    ''')
    rows = cursor.fetchall()
    conn.close()

    posts = []
    for r in rows:
        posts.append({
            "id": r["id"],
            "title": r["title"],
            "text": r["text"],
            "timestamp": r["timestamp"],
            "likes": json.loads(r["likes"] or '[]'),
            "views": json.loads(r["views"] or '[]'),
            "author": {"id": r["author_id"], "username": r["author_username"]}
        })
    return posts


def _toggle_engagement(post_id: int, field: str, user_id: int) -> List[int]:
    """Add user_id to the post's field array (likes or views) if not already present."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'SELECT {field} FROM posts WHERE id = ?', (post_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    current: List[int] = json.loads(row[field] or '[]')
    if user_id not in current:
        current.append(user_id)
        cursor.execute(
            f'UPDATE posts SET {field} = ? WHERE id = ?',
            (json.dumps(current), post_id)
        )
        conn.commit()
        # Invalidate the recent posts cache
        redis_client.delete('posts:recent')

    conn.close()
    return current


@app.post("/posts/{post_id}/like")
def like_post(post_id: int, body: EngagementRequest):
    likes = _toggle_engagement(post_id, 'likes', body.user_id)
    return {"post_id": post_id, "likes": likes, "total": len(likes)}


@app.post("/posts/{post_id}/view")
def view_post(post_id: int, body: EngagementRequest):
    views = _toggle_engagement(post_id, 'views', body.user_id)
    return {"post_id": post_id, "views": views, "total": len(views)}

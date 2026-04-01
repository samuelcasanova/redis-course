from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pydantic import BaseModel
from typing import List
import sqlite3
import redis
import json
import os
import time
import redis.asyncio as aioredis

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
async_redis_client = aioredis.Redis(host='redis', port=6379, db=0, decode_responses=True)
db_path = os.path.join('/data/sqlite', 'engagement.db')

def log_info(msg: str):
    print(msg)
    try:
        redis_client.xadd("system_logs", {"level": "info", "message": str(msg)})
    except Exception:
        pass

def log_error(msg: str):
    print(f"ERROR: {msg}")
    try:
        redis_client.xadd("system_logs", {"level": "error", "message": str(msg)})
    except Exception:
        pass


class UserCreate(BaseModel):
    username: str
    email: str
    bio: str = ""


class EngagementRequest(BaseModel):
    user_id: int


class FollowRequest(BaseModel):
    follower_id: int


class PostCreate(BaseModel):
    user_id: int
    title: str
    text: str


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
        redis_client.xadd("domain_events", {
            "type": "new_user",
            "user_id": str(user_id),
            "username": user.username
        })
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
        log_info("[CACHE HIT] All Users")
        return json.loads(cached_users)

    log_info("[CACHE MISS] Fetching All Users from DB")
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
    cache_key = "users:top"
    
    # Try Cache First
    cached_top = redis_client.get(cache_key)
    if cached_top:
        log_info("[CACHE HIT] Top Users")
        return json.loads(cached_top)

    log_info("[CACHE MISS] Top Users - Fetching from DB")
    time.sleep(3)  # Simulate slow DB operation
    
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
    
    # Store in Cache with 60s TTL
    results = [dict(row) for row in rows]
    redis_client.setex(cache_key, 60, json.dumps(results))
    
    return results


@app.get("/users/{user_id}")
def get_user(user_id: int):
    cache_key = f"user:profile:{user_id}"

    # Try Cache First
    cached_profile = redis_client.get(cache_key)
    if cached_profile:
        log_info(f"[CACHE HIT] User {user_id}")
        return json.loads(cached_profile)

    log_info(f"[CACHE MISS] User {user_id} - Fetching from DB")
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


@app.get("/posts/trending")
def get_trending_posts():
    """Return top 10 trending posts ranked by likes + views using a Redis Sorted Set."""
    trending_key = "posts:trending"

    # Fetch top 10 post IDs (highest score first) with their scores
    top_entries = redis_client.zrevrange(trending_key, 0, 9, withscores=True)

    if not top_entries:
        return []

    post_ids = [int(post_id) for post_id, _ in top_entries]
    scores = {int(post_id): score for post_id, score in top_entries}

    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(post_ids))
    cursor.execute(
        f'''
        SELECT p.id, p.title, p.text, p.timestamp, p.likes, p.views,
               u.id as author_id, u.username as author_username
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.id IN ({placeholders})
        ''',
        post_ids
    )
    rows = cursor.fetchall()
    conn.close()

    # Build result, preserving the ranking order from Redis
    row_map = {r["id"]: r for r in rows}
    posts = []
    for post_id in post_ids:
        r = row_map.get(post_id)
        if r:
            posts.append({
                "id": r["id"],
                "title": r["title"],
                "text": r["text"],
                "timestamp": r["timestamp"],
                "likes": json.loads(r["likes"] or '[]'),
                "views": json.loads(r["views"] or '[]'),
                "score": int(scores[post_id]),
                "author": {"id": r["author_id"], "username": r["author_username"]}
            })
    return posts


@app.post("/posts")
def create_post(post: PostCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO posts (user_id, title, text) VALUES (?, ?, ?)',
        (post.user_id, post.title, post.text)
    )
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()

    redis_client.xadd("domain_events", {
        "type": "new_post",
        "post_id": str(post_id),
        "user_id": str(post.user_id),
        "title": post.title
    })

    # Invalidate recent posts cache
    redis_client.delete('posts:recent')
    
    # -----------------------------------------
    # REDIS LISTS: FAN-OUT ON WRITE (TIMELINE)
    # -----------------------------------------
    # 1. Get all followers of the author
    follower_ids = redis_client.smembers(f"user:{post.user_id}:followers")
    
    # 2. Push this post ID to every follower's timeline
    pipe = redis_client.pipeline()
    for follower_id in follower_ids:
        timeline_key = f"timeline:{follower_id}"
        pipe.lpush(timeline_key, str(post_id))
        # Keep only the latest 100 posts to save memory
        pipe.ltrim(timeline_key, 0, 99)
    
    # We also add it to the user's own timeline
    timeline_key = f"timeline:{post.user_id}"
    pipe.lpush(timeline_key, str(post_id))
    pipe.ltrim(timeline_key, 0, 99)
    
    pipe.execute()

    return {"id": post_id, "message": "Post created and fanned out"}


@app.get("/users/{user_id}/timeline")
def get_timeline(user_id: int):
    timeline_key = f"timeline:{user_id}"
    
    # -----------------------------------------
    # LAZY HYDRATION (CACHE-ASIDE FOR LISTS)
    # -----------------------------------------
    if not redis_client.exists(timeline_key):
        log_info(f"[CACHE MISS] Hydrating timeline for user {user_id}")
        time.sleep(3)  # Simulate slow DB operation for calculating the timeline
        following_ids = redis_client.smembers(f"user:{user_id}:following")
        
        # We want to see posts from our followings + our own posts
        ids_to_fetch = list(following_ids) + [str(user_id)]
        placeholders = ','.join('?' * len(ids_to_fetch))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch the latest 50 posts from these users (newest first)
        cursor.execute(f'''
            SELECT id FROM posts 
            WHERE user_id IN ({placeholders}) 
            ORDER BY timestamp DESC LIMIT 50
        ''', ids_to_fetch)
        
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            post_ids = [row["id"] for row in rows]
            # When creating list from sorted results (newest first), 
            # RPUSH ensures newest stays at the beginning (left) of the list
            pipe = redis_client.pipeline()
            pipe.rpush(timeline_key, *post_ids)
            pipe.expire(timeline_key, 86400) # Expire in 24 hours
            pipe.execute()
        else:
            return [] # No posts found
    else:
        log_info(f"[CACHE HIT] Timeline for user {user_id}")
        # Reset expiration so active users stay cached lengthily
        redis_client.expire(timeline_key, 86400)

    # -----------------------------------------
    # READ TIMELINE FROM REDIS
    # -----------------------------------------
    # Fetch exactly the top 20 post IDs from the Redis List instantly
    post_ids = redis_client.lrange(timeline_key, 0, 19)
    if not post_ids:
        return []

    # Map those rapid IDs to their actual SQL records
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(post_ids))
    cursor.execute(
        f'''
        SELECT p.id, p.title, p.text, p.timestamp, p.likes, p.views,
               u.id as author_id, u.username as author_username
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.id IN ({placeholders})
        ''',
        post_ids
    )
    rows = cursor.fetchall()
    conn.close()

    # Re-order the results exactly as Redis returned them
    row_map = {str(r["id"]): r for r in rows}
    
    posts = []
    for pid in post_ids:
        r = row_map.get(str(pid))
        if r:
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


@app.get("/posts/recent")
def get_recent_posts():
    time.sleep(3)  # Simulate slow DB operation
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
        # Increment the post's score in the trending Sorted Set
        redis_client.zincrby('posts:trending', 1, str(post_id))

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


def _get_user_row(cursor, user_id: int):
    cursor.execute('SELECT id, username, email, bio, followers FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row


def _user_summary(row) -> dict:
    return {"id": row["id"], "username": row["username"], "email": row["email"], "bio": row["bio"]}


@app.post("/users/{user_id}/follow")
def follow_user(user_id: int, body: FollowRequest):
    """Add body.follower_id to user_id's followers list (idempotent)."""
    if user_id == body.follower_id:
        raise HTTPException(status_code=400, detail="A user cannot follow themselves")

    conn = get_db_connection()
    cursor = conn.cursor()
    row = _get_user_row(cursor, user_id)

    followers: List[int] = json.loads(row["followers"] or '[]')
    if body.follower_id not in followers:
        followers.append(body.follower_id)
        cursor.execute('UPDATE users SET followers = ? WHERE id = ?', (json.dumps(followers), user_id))
        conn.commit()
        redis_client.delete(f"user:profile:{user_id}")
        redis_client.sadd(f"user:{user_id}:followers", body.follower_id)
        redis_client.sadd(f"user:{body.follower_id}:following", user_id)
        
        redis_client.xadd("domain_events", {
            "type": "new_follower",
            "user_id": str(user_id),
            "follower_id": str(body.follower_id)
        })

    conn.close()
    return {"user_id": user_id, "followers": followers, "total": len(followers)}


@app.post("/users/{user_id}/unfollow")
def unfollow_user(user_id: int, body: FollowRequest):
    """Remove body.follower_id from user_id's followers list."""
    conn = get_db_connection()
    cursor = conn.cursor()
    row = _get_user_row(cursor, user_id)

    followers: List[int] = json.loads(row["followers"] or '[]')
    if body.follower_id in followers:
        followers.remove(body.follower_id)
        cursor.execute('UPDATE users SET followers = ? WHERE id = ?', (json.dumps(followers), user_id))
        conn.commit()
        redis_client.delete(f"user:profile:{user_id}")
        redis_client.srem(f"user:{user_id}:followers", body.follower_id)
        redis_client.srem(f"user:{body.follower_id}:following", user_id)

    conn.close()
    return {"user_id": user_id, "followers": followers, "total": len(followers)}


@app.get("/users/{user_id}/followers")
def get_followers(user_id: int):
    """Return the list of user profiles who follow user_id."""
    follower_ids = redis_client.smembers(f"user:{user_id}:followers")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if not follower_ids:
        # Check if user actually exists
        _get_user_row(cursor, user_id)
        conn.close()
        return []

    follower_ids_list = list(follower_ids)
    placeholders = ','.join('?' * len(follower_ids_list))
    cursor.execute(
        f'SELECT id, username, email, bio FROM users WHERE id IN ({placeholders})',
        follower_ids_list
    )
    results = [_user_summary(r) for r in cursor.fetchall()]
    conn.close()
    return results


@app.get("/users/{user_id}/following")
def get_following(user_id: int):
    """Return the list of user profiles that user_id follows."""
    following_ids = redis_client.smembers(f"user:{user_id}:following")
    
    conn = get_db_connection()
    cursor = conn.cursor()

    if not following_ids:
        # Verify the user exists first
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")
        conn.close()
        return []

    following_ids_list = list(following_ids)
    placeholders = ','.join('?' * len(following_ids_list))
    cursor.execute(
        f'SELECT id, username, email, bio FROM users WHERE id IN ({placeholders})',
        following_ids_list
    )
    results = [_user_summary(r) for r in cursor.fetchall()]
    conn.close()
    return results


@app.get("/users/{user_id}/mutual_following/{other_user_id}")
def get_mutual_following(user_id: int, other_user_id: int):
    """Return the list of user profiles that BOTH users follow using SINTER."""
    # This is where Redis Sets shine. O(N*M) mathematics done entirely in memory.
    mutual_ids = redis_client.sinter(f"user:{user_id}:following", f"user:{other_user_id}:following")
    
    if not mutual_ids:
        return []
        
    mutual_ids_list = list(mutual_ids)
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(mutual_ids_list))
    cursor.execute(
        f'SELECT id, username, email, bio FROM users WHERE id IN ({placeholders})',
        mutual_ids_list
    )
    results = [_user_summary(r) for r in cursor.fetchall()]
    conn.close()
    return results


@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: int):
    await websocket.accept()
    pubsub = async_redis_client.pubsub()
    await pubsub.subscribe(f"notifications:{user_id}", "notifications:all")
    log_info(f"WebSocket connected for user {user_id}")

    # Start a background task to receive client disconnect signals
    async def listen_for_disconnect():
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass

    disconnect_task = asyncio.create_task(listen_for_disconnect())

    try:
        while not disconnect_task.done():
            # Awaits new messages for up to 1 second
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get('type') == 'message':
                await websocket.send_text(str(message['data']))
    except Exception as e:
        log_error(f"WS Exception: {e}")
    finally:
        disconnect_task.cancel()
        await pubsub.unsubscribe()
        await pubsub.close()
        log_info(f"WebSocket disconnected for user {user_id}")

import sqlite3
import redis
import json
import time

# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

import os

# Ensure .data directory exists
data_dir = '/data/sqlite'
os.makedirs(data_dir, exist_ok=True)

# Connect to SQLite
db_path = os.path.join(data_dir, 'engagement.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def setup_db():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        bio TEXT
    )
    ''')
    
    users = [
        ('alice123', 'alice@example.com', 'Tech enthusiast & coder'),
        ('bob_builder', 'bob@example.com', 'I build things'),
        ('charlie_chap', 'charlie@example.com', 'Always smiling'),
        ('dana_scully', 'dana@example.com', 'The truth is out there')
    ]
    
    for user in users:
        cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, bio)
        VALUES (?, ?, ?)
        ''', user)
    conn.commit()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        text TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        likes TEXT DEFAULT '[]',
        views TEXT DEFAULT '[]',
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('SELECT COUNT(*) FROM posts')
    if cursor.fetchone()[0] == 0:
        sample_posts = [
            (1, 'Hello World!', 'This is my first post on this awesome new platform!'),
            (2, 'Building things', 'Just sharing a quick update on my latest construction project.'),
            (3, 'Smile everyday', 'A simple reminder to keep smiling and stay positive.'),
            (4, 'The truth', 'I have found new evidence. The truth is definitely out there.'),
            (1, 'Coding tips', 'Remember to always use a cache for frequently accessed data.'),
            (2, 'Tools of the trade', 'What is your favorite hammer? Let me know in the comments.'),
            (3, 'Joke of the day', 'Why did the developer go broke? Because he used up all his cache!'),
            (4, 'Unexplained phenomena', 'Did anyone else see those lights in the sky last night?'),
            (1, 'React + Vite', 'Loving the new developer experience with Vite and React.'),
            (2, 'Architecture', 'Good foundations are key, whether in buildings or software.')
        ]
        
        for post in sample_posts:
            cursor.execute('''
            INSERT INTO posts (user_id, title, text, likes, views)
            VALUES (?, ?, ?, '[]', '[]')
            ''', post)
        conn.commit()
    
def get_user_profile(user_id: int):
    cache_key = f"user:profile:{user_id}"
    
    # 1. Try Cache First
    start_time = time.time()
    cached_profile = redis_client.get(cache_key)
    
    if cached_profile:
        ms_time = (time.time() - start_time)*1000
        print(f"[CACHE HIT] Retrieved user {user_id} in {ms_time:.2f}ms")
        return json.loads(cached_profile)
    
    # 2. Cache Miss -> Query Database
    print(f"[CACHE MISS] Fetching user {user_id} from SQLite...")
    start_time = time.time()
    cursor.execute('SELECT id, username, email, bio FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    
    if row:
        profile = {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'bio': row[3]
        }
        
        # 3. Store in Cache (with TTL of 1 hour)
        redis_client.setex(cache_key, 3600, json.dumps(profile))
        
        ms_time = (time.time() - start_time)*1000
        print(f"[DB HIT] Retrieved user {user_id} in {ms_time:.2f}ms")
        return profile
    
    return None

if __name__ == '__main__':
    print("Setting up the database...")
    setup_db()
    print("Database setup complete. 4 user profiles are ready.\n")
    
    # Test fetching User 1 (Alice)
    print("--- Fetching User 1 (First Time) ---")
    user1 = get_user_profile(1)
    print(user1)
    
    print("\n--- Fetching User 1 (Second Time) ---")
    user1_cached = get_user_profile(1)
    print(user1_cached)
    
    # Test fetching User 2 (Bob)
    print("\n--- Fetching User 2 (First Time) ---")
    user2 = get_user_profile(2)
    print(user2)
    
    print("\n--- Fetching User 2 (Second Time) ---")
    user2_cached = get_user_profile(2)
    print(user2_cached)

    # Clean up connections
    conn.close()

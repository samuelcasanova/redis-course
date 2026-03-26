import sqlite3
import redis
import json
import time
import os
import random

# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# Ensure .data directory exists
data_dir = '/data/sqlite'
os.makedirs(data_dir, exist_ok=True)

# Connect to SQLite
db_path = os.path.join(data_dir, 'engagement.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

FIRST_NAMES = [
    'alice', 'bob', 'charlie', 'dana', 'eve', 'frank', 'grace', 'han',
    'iris', 'jake', 'karen', 'leo', 'maya', 'nick', 'olivia', 'peter',
    'quinn', 'rosa', 'sam', 'tina', 'uma', 'victor', 'wanda', 'xena',
    'yara', 'zoe', 'aaron', 'bella', 'carlos', 'diana', 'ethan', 'fiona',
    'george', 'holly', 'ivan', 'julia', 'kevin', 'luna', 'marco', 'nina',
    'oscar', 'pam', 'ray', 'sara', 'tom', 'ursula', 'vince', 'wendy',
]

LAST_NAMES = [
    'smith', 'jones', 'brown', 'taylor', 'wilson', 'davis', 'garcia',
    'miller', 'moore', 'martin', 'lee', 'white', 'harris', 'clark',
    'lewis', 'robinson', 'walker', 'hall', 'allen', 'young', 'king',
    'wright', 'scott', 'green', 'adams', 'baker', 'nelson', 'carter',
]

BIOS = [
    'Tech enthusiast & coder', 'I build things', 'Always smiling',
    'The truth is out there', 'Security researcher & CTF addict',
    'Coffee drinker. Ex-marine.', 'Pioneering software one bug at a time',
    'Never tell me the odds', 'Journalist. Coffee. Speed.',
    'Cool, cool, cool. No doubt.', 'Data scientist by day, chef by night',
    'Football. Family. Mate.', 'Fixer. Wine lover.', 'Trust no one.',
    'Friendly neighbourhood developer', 'Veteran. Team player.',
    'Tough. Mysterious. Rides motorcycles.', 'Reality warper & hex caster',
    'Warrior princess.', 'Sailor. Fighter. Ironborn.',
]


def _generate_users(count: int = 25000):
    """Generate `count` unique (username, email, bio) tuples."""
    seen = set()
    users = []
    counter = 0
    while len(users) < count:
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        username = f"{first}_{last}{counter}"
        if username in seen:
            counter += 1
            continue
        seen.add(username)
        email = f"{username}@example.com"
        bio = random.choice(BIOS)
        users.append((username, email, bio))
        counter += 1
    return users


USERS = _generate_users(25000)

SAMPLE_POSTS = [
    (1,  'Hello World!',           'This is my first post on this awesome new platform!'),
    (2,  'Building things',        'Just sharing a quick update on my latest construction project.'),
    (3,  'Smile everyday',         'A simple reminder to keep smiling and stay positive.'),
    (4,  'The truth',              'I have found new evidence. The truth is definitely out there.'),
    (5,  'Security 101',           'Always rotate your API keys, folks. Learned that the hard way.'),
    (6,  'Morning coffee ritual',  'Black coffee, no sugar. Fight me.'),
    (7,  'Debugging is art',       'Finding a bug after 6 hours: priceless. Using print() shamelessly.'),
    (8,  'The Kessel Run',         'Made it in 12 parsecs. Pretty proud of that.'),
    (9,  'Breaking news',          'Big story dropping tonight. Stay tuned.'),
    (10, 'Nine-Nine!',             'Just solved my first algorithm challenge. Noice.'),
    (1,  'Coding tips',            'Remember to always use a cache for frequently accessed data.'),
    (2,  'Tools of the trade',     'What is your favorite hammer? Let me know in the comments.'),
    (3,  'Joke of the day',        'Why did the developer go broke? Because he used up all his cache!'),
    (4,  'Unexplained phenomena',  'Did anyone else see those lights in the sky last night?'),
    (1,  'React + Vite',           'Loving the new developer experience with Vite and React.'),
    (2,  'Architecture',           'Good foundations are key, whether in buildings or software.'),
    (11, 'Breaking a story',       'Sources confirmed. This changes everything.'),
    (12, 'The beautiful game',     'Football is life. Redis is also life.'),
    (13, 'My ML pipeline',         'Switched to Polars. Training time dropped by 60%. Mind blown.'),
    (14, 'Trust no one',           'Threat model everything. Assume breach.'),
]


def setup_db():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        bio TEXT,
        followers TEXT DEFAULT '[]'
    )
    ''')

    # Add followers column if upgrading an existing DB
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN followers TEXT DEFAULT '[]'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        print("Inserting users...")
        cursor.executemany('''
        INSERT OR IGNORE INTO users (username, email, bio)
        VALUES (?, ?, ?)
        ''', USERS)
        conn.commit()

    # Fetch the actual IDs assigned to users
    cursor.execute('SELECT id FROM users')
    all_user_ids = [row[0] for row in cursor.fetchall()]

    # Seed followers: each user gets 10-300 random followers (not themselves)
    cursor.execute('SELECT COUNT(*) FROM users WHERE followers != ?', ('[]',))
    if cursor.fetchone()[0] == 0:
        print("Seeding followers... (this might take a few seconds)")
        updates = []
        for uid in all_user_ids:
            # Picking a random sample efficiently without loading 25k items into array per iteration
            count = random.randint(10, 300)
            follower_set = set()
            while len(follower_set) < count:
                f_id = random.choice(all_user_ids)
                if f_id != uid:
                    follower_set.add(f_id)
            updates.append((json.dumps(list(follower_set)), uid))
            
            # Batch apply updates to avoid memory explosion
            if len(updates) >= 5000:
                cursor.executemany('UPDATE users SET followers = ? WHERE id = ?', updates)
                updates = []
                
        if updates:
            cursor.executemany('UPDATE users SET followers = ? WHERE id = ?', updates)
        conn.commit()
        print(f"Seeded followers for {len(all_user_ids)} users.")

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
        print("Generating posts...")
        post_inserts = []
        # Generate 100,000 posts to severely stress the unindexed JOIN for /users/top
        for i in range(100000):
            uid = random.choice(all_user_ids)
            base_post = random.choice(SAMPLE_POSTS)
            title = f"{base_post[1]} - {i}"
            text = base_post[2]
            
            num_likes = random.randint(10, 50)
            num_views = random.randint(50, 200)
            
            like_set = set()
            while len(like_set) < num_likes:
                like_set.add(random.choice(all_user_ids))
            
            view_set = set()
            while len(view_set) < num_views:
                view_set.add(random.choice(all_user_ids))
                
            post_inserts.append((uid, title, text, json.dumps(list(like_set)), json.dumps(list(view_set))))
            
            if len(post_inserts) >= 10000:
                cursor.executemany('''
                INSERT INTO posts (user_id, title, text, likes, views)
                VALUES (?, ?, ?, ?, ?)
                ''', post_inserts)
                post_inserts = []
                
        if post_inserts:
            cursor.executemany('''
            INSERT INTO posts (user_id, title, text, likes, views)
            VALUES (?, ?, ?, ?, ?)
            ''', post_inserts)
            
        conn.commit()
        print("Seeded 100,000 posts with random likes and views.")

    # Hydrate the posts:trending Sorted Set from SQLite
    trending_key = "posts:trending"
    if redis_client.zcard(trending_key) == 0:
        print("Hydrating posts:trending Sorted Set in Redis...")
        cursor.execute("SELECT id, likes, views FROM posts")
        rows = cursor.fetchall()
        pipe = redis_client.pipeline()
        for row in rows:
            post_id = row[0]
            likes = len(json.loads(row[1] or '[]'))
            views = len(json.loads(row[2] or '[]'))
            score = likes + views
            pipe.zadd(trending_key, {str(post_id): score})
        pipe.execute()
        print(f"Hydrated {len(rows)} posts into posts:trending.")

    # Hydrate the Followers and Following Sets from SQLite
    if not redis_client.exists("user:1:followers") and not redis_client.exists("user:1:following"):
        print("Hydrating followers & following Sets in Redis...")
        cursor.execute("SELECT id, followers FROM users")
        user_rows = cursor.fetchall()
        pipe = redis_client.pipeline()
        for row in user_rows:
            user_id = row[0]
            followers = json.loads(row[1] or '[]')
            if followers:
                pipe.sadd(f"user:{user_id}:followers", *followers)
                for f_id in followers:
                    pipe.sadd(f"user:{f_id}:following", user_id)
        pipe.execute()
        print(f"Hydrated followers and following sets for {len(user_rows)} users.")


def get_user_profile(user_id: int):
    cache_key = f"user:profile:{user_id}"

    # 1. Try Cache First
    start_time = time.time()
    cached_profile = redis_client.get(cache_key)

    if cached_profile:
        ms_time = (time.time() - start_time) * 1000
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

        ms_time = (time.time() - start_time) * 1000
        print(f"[DB HIT] Retrieved user {user_id} in {ms_time:.2f}ms")
        return profile

    return None


if __name__ == '__main__':
    print("Setting up the database...")
    setup_db()
    print(f"Database setup complete. {len(USERS)} user profiles are ready.\n")

    # Test cache behaviour for User 1
    print("--- Fetching User 1 (First Time) ---")
    user1 = get_user_profile(1)
    print(user1)

    print("\n--- Fetching User 1 (Second Time — should be cached) ---")
    user1_cached = get_user_profile(1)
    print(user1_cached)

    # Clean up connections
    conn.close()

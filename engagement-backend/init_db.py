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


def _generate_users(count: int = 600):
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


USERS = _generate_users(600)

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

    for user in USERS:
        cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, bio)
        VALUES (?, ?, ?)
        ''', user)
    conn.commit()

    # Fetch the actual IDs assigned to users
    cursor.execute('SELECT id FROM users')
    all_user_ids = [row[0] for row in cursor.fetchall()]

    # Seed followers: each user gets 10-100 random followers (not themselves)
    cursor.execute('SELECT COUNT(*) FROM users WHERE followers != ?', ('[]',))
    if cursor.fetchone()[0] == 0:
        for uid in all_user_ids:
            pool = [i for i in all_user_ids if i != uid]
            count = random.randint(10, 300)
            followers = json.dumps(random.sample(pool, min(count, len(pool))))
            cursor.execute('UPDATE users SET followers = ? WHERE id = ?', (followers, uid))
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
        for post in SAMPLE_POSTS:
            num_likes = random.randint(20, 50)
            num_views = random.randint(100, 500)
            likes = json.dumps(random.sample(all_user_ids, min(num_likes, len(all_user_ids))))
            views = json.dumps(random.sample(all_user_ids, min(num_views, len(all_user_ids))))
            cursor.execute('''
            INSERT INTO posts (user_id, title, text, likes, views)
            VALUES (?, ?, ?, ?, ?)
            ''', (post[0], post[1], post[2], likes, views))
        conn.commit()
        print(f"Seeded {len(SAMPLE_POSTS)} posts with random likes and views.")


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

import redis
import json
import time

# Connect to local Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def get_user_from_db(user_id):
    """
    Simulates a database lookup.
    """
    print(f"(DB) Fetching user {user_id} from database...")
    time.sleep(0.5)  # Simulate DB latency
    db_users = {
        "user:1": {"id": 1, "name": "Alice", "email": "alice@example.com"},
        "user:2": {"id": 2, "name": "Bob", "email": "bob@example.com"}
    }
    return db_users.get(f"user:{user_id}")


def get_user_cache_aside(user_id):
    """
    Implementation of the Cache-Aside pattern.
    1. Check cache.
    2. If miss, fetch from DB.
    3. Update cache.
    4. Return data.
    """
    cache_key = f"user_cache:{user_id}"

    # 1. Try to get from Redis
    cached_user = r.get(cache_key)
    if cached_user:
        print(f"(Cache) Hit for user {user_id}!")
        return json.loads(cached_user)

    # 2. Cache miss, go to DB
    print(f"(Cache) Miss for user {user_id}...")
    user_data = get_user_from_db(user_id)

    if user_data:
        # 3. Store in cache for future requests (with TTL)
        r.setex(cache_key, 300, json.dumps(user_data))
        return user_data

    return None


def simulate_cache_aside():
    print("--- Simulating Cache-Aside Pattern ---")
    user_id = "1"

    # Ensure clear state
    r.delete(f"user_cache:{user_id}")

    # First access (Miss)
    print("\n--- First Access ---")
    user = get_user_cache_aside(user_id)
    print(f"Result: {user}")

    # Second access (Hit)
    print("\n--- Second Access ---")
    user = get_user_cache_aside(user_id)
    print(f"Result: {user}")


if __name__ == "__main__":
    try:
        r.ping()
        simulate_cache_aside()
    except redis.ConnectionError:
        print("Error: Could not connect to Redis. "
              "Please ensure the Redis server is running.")

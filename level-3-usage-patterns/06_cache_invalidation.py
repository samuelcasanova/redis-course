import redis
import json
import time

# Connect to local Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def update_user_db_and_cache(user_id, updated_data):
    """
    Shows manual invalidation: update DB and then delete cache entry.
    """
    cache_key = f"user_cache:{user_id}"

    print(f"(DB) Updating user {user_id} in database...")
    # (Simulated DB update)

    print(f"(Cache) Invalidating cache for user {user_id}...")
    r.delete(cache_key)


def get_user_with_ttl(user_id):
    """
    Shows TTL-based invalidation.
    """
    cache_key = f"user_cache:{user_id}"
    cached_user = r.get(cache_key)

    if cached_user:
        return json.loads(cached_user)

    print(f"Fetching from DB for user {user_id}...")
    # (Simulated DB fetch)
    user_data = {"id": user_id, "name": "Alice", "updated_at": time.time()}

    # Set with short TTL for demo
    r.setex(cache_key, 2, json.dumps(user_data))
    return user_data


def simulate_invalidation():
    print("--- Simulating Cache Invalidation ---")
    user_id = "1"

    # 1. Manual Invalidation
    print("\n[Manual Invalidation Demo]")
    # Populate cache
    get_user_with_ttl(user_id)
    print(f"Cache key exists: {r.exists(f'user_cache:{user_id}')}")

    # Update and invalidate
    update_user_db_and_cache(user_id, {"name": "Alice Updated"})
    print(f"Cache key exists: {r.exists(f'user_cache:{user_id}')}")

    # 2. TTL Demo
    print("\n[TTL Invalidation Demo]")
    get_user_with_ttl(user_id)
    print("Wait for 3 seconds...")
    time.sleep(3)
    print(f"Cache key exists after sleep: {r.exists(f'user_cache:{user_id}')}")


if __name__ == "__main__":
    try:
        r.ping()
        simulate_invalidation()
    except redis.ConnectionError:
        print("Error: Could not connect to Redis. "
              "Please ensure the Redis server is running.")

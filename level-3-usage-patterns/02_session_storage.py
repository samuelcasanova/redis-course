import redis
import json
import uuid
import time

# Connect to local Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def create_session(user_data, expires_in=3600):
    """
    Creates a new session in Redis for a user.
    """
    session_id = str(uuid.uuid4())
    key = f"session:{session_id}"

    # Store user data as a hash
    r.hset(key, mapping=user_data)
    # Set session expiration
    r.expire(key, expires_in)

    return session_id


def get_session(session_id):
    """
    Retrieves session data from Redis.
    """
    key = f"session:{session_id}"
    return r.hgetall(key)


def update_session(session_id, data):
    """
    Updates existing session data.
    """
    key = f"session:{session_id}"
    if r.exists(key):
        r.hset(key, mapping=data)
        return True
    return False


def delete_session(session_id):
    """
    Deletes a session.
    """
    return r.delete(f"session:{session_id}")


def simulate_sessions():
    print("--- Simulating Session Storage ---")

    # 1. Create a session
    user = {
        "user_id": "user_123",
        "username": "jdoe",
        "role": "admin",
        "last_login": str(int(time.time()-1234))
    }

    session_id = create_session(user, expires_in=10)
    print(f"Created session: {session_id}")

    # 2. Retrieve session
    stored_session = get_session(session_id)
    print(f"Retrieved session: {json.dumps(stored_session, indent=2)}")

    # 3. Update session
    print("Updating session last_login...")
    update_session(session_id, {"last_login": str(int(time.time()))})

    # 4. Show updated session
    updated_session = get_session(session_id)
    print(f"Updated session: {json.dumps(updated_session, indent=2)}")

    # 5. Delete session
    delete_session(session_id)
    print("Deleted session.")

    # 6. Verify deletion
    if not get_session(session_id):
        print("Verification: Session successfully removed.")


if __name__ == "__main__":
    try:
        r.ping()
        simulate_sessions()
    except redis.ConnectionError:
        print("Error: Could not connect to Redis. "
              "Please ensure the Redis server is running.")

import redis
import time

# Connect to local Redis (ensure redis-server is running)
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def check_rate_limit(user_id, limit=5, window=10):
    """
    Checks if a user has exceeded their request limit within a time window.
    This implementation uses a simple fixed window counter.

    :param user_id: ID or IP of the user
    :param limit: Maximum number of requests allowed
    :param window: Time window in seconds
    :return: Tuple (is_limited, current_count)
    """
    # Calculate the current time chunk (e.g., current 10-second window)
    current_time_window = int(time.time() // window)
    key = f"rate_limit:{user_id}:{current_time_window}"

    # Increment the counter for this window
    current_count = r.incr(key)

    # If this is the first request in the window, set an expiration
    # We set it to window * 2 to ensure it doesn't expire prematurely
    # and cleans up automatically.
    if current_count == 1:
        r.expire(key, window * 2)

    if current_count > limit:
        return True, current_count

    return False, current_count


def simulate_requests():
    user_ip = "192.168.1.10"
    limit = 5
    window_seconds = 10

    print(f"--- Simulating Rate Limiting ({limit} per {window_seconds}s) ---")

    for i in range(1, 10):
        is_limited, count = check_rate_limit(user_ip, limit, window_seconds)

        if is_limited:
            print(f"[Request {i}] REJECTED! Limit exceeded (Count: {count})")
        else:
            print(f"[Request {i}] ACCEPTED. (Count: {count})")

        # Simulate some delay between requests
        time.sleep(1)

    print("\nWaiting for the time window to reset (10 seconds)...")
    time.sleep(10)

    print("\n--- Sending request after window reset ---")
    is_limited, count = check_rate_limit(user_ip, limit, window_seconds)
    if is_limited:
        print(f"[Request 10] REJECTED! Rate exceeded (Count: {count})")
    else:
        print(f"[Request 10] ACCEPTED. (Count: {count})")

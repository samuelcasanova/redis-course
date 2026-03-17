import redis
import time

# Connect to local Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def publish_messages():
    """Sends a few sample messages to the subscriber."""
    print("--- Sending sample messages to 'notifications' ---")

    messages = [
        "First message: Hello!",
        "Second message: User #123 logged in.",
        "Third message: Server status: OK.",
        "DONE: Closing channel demo."
    ]

    for msg in messages:
        num_subscribers = r.publish('notifications', msg)
        print(f"[#] Published to notifications: '{msg}' ({num_subscribers} received it)")
        time.sleep(1)  # Slow it down for demo purposes


if __name__ == "__main__":
    try:
        r.ping()
        publish_messages()
    except redis.ConnectionError:
        print("Error: Could not connect to Redis. "
              "Please ensure the Redis server is running.")

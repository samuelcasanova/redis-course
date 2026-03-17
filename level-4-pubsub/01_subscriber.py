import redis

# 1. Connect to Redis (decode_responses=True gives us strings instead of bytes)
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def start_subscriber():
    """
    Subscribes to a channel and prints every message it receives.
    """
    # Create a pubsub object
    pubsub = r.pubsub()

    # Subscribe to a specific channel
    print("[*] Subscribing to 'notifications' channel...")
    pubsub.subscribe('notifications')

    # Pub/Sub is blocking. We can iterate over the messages in a loop.
    print("[*] Waiting for messages. Press Ctrl+C to stop.")

    for message in pubsub.listen():
        # The first message is usually a 'subscribe' confirmation
        if message['type'] == 'message':
            data = message['data']
            channel = message['channel']
            print(f"Received from [{channel}]: {data}")



if __name__ == "__main__":
    try:
        r.ping()
        start_subscriber()
    except redis.ConnectionError:
        print("Error: Could not connect to Redis. "
              "Please ensure the Redis server is running.")
    except KeyboardInterrupt:
        print("\n[*] Stopping subscriber.")

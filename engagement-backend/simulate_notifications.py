import redis
import time
import json
import random

# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

USER_ID = 1234
CHANNEL = f"notifications:{USER_ID}"

NOTIFICATIONS = [
    {"title": "New Follower", "message": "alice_smith started following you!"},
    {"title": "New Follower", "message": "bob_wizard started following you!"},
    {"title": "Post Liked", "message": "charlie_dev liked your post"},
    {"title": "Post Liked", "message": "dana_ninja liked your post"},
    {"title": "New Timeline Post", "message": "alice_smith just published a new post. Check it out!"},
    {"title": "System Update", "message": "We are deploying a new version of the app in 5 minutes."},
]

print(f"Starting notification simulation for user {USER_ID} on channel '{CHANNEL}'...")
print("Press Ctrl+C to stop.")

try:
    while True:
        event = random.choice(NOTIFICATIONS)
        # Publish the event exactly the same way the backend would
        published = redis_client.publish(CHANNEL, json.dumps(event))
        print(f"[{time.strftime('%X')}] Sent: '{event['title']}' (Received by {published} clients)")
        time.sleep(3)
except KeyboardInterrupt:
    print("\nSimulation stopped.")

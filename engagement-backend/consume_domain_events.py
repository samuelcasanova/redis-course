import redis
import time

# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

STREAM_KEY = 'domain_events'
LAST_ID_KEY = 'consumer:domain_events:last_id'

def get_last_id():
    last_id = redis_client.get(LAST_ID_KEY)
    return last_id if last_id else '0-0'

def set_last_id(last_id):
    redis_client.set(LAST_ID_KEY, last_id)

def send_welcome_email(user_id, username):
    print(f"[\u2709\ufe0f EMAIL] Sending welcome email to new user {user_id} ({username})...")

def send_new_follower_email(user_id, follower_id):
    print(f"[\u2709\ufe0f EMAIL] Notifying user {user_id} that user {follower_id} started following them!")

def main():
    print("Starting domain events consumer...")
    last_id = get_last_id()
    print(f"Resuming from ID: {last_id}")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            # Block for 5 seconds waiting for new events
            # XREAD BLOCK 5000 STREAMS domain_events <last_id>
            events = redis_client.xread({STREAM_KEY: last_id}, block=5000, count=10)
            
            if events:
                for stream_name, messages in events:
                    for message_id, message_data in messages:
                        event_type = message_data.get('type')
                        
                        if event_type == 'new_user':
                            send_welcome_email(message_data.get('user_id'), message_data.get('username'))
                        elif event_type == 'new_follower':
                            send_new_follower_email(message_data.get('user_id'), message_data.get('follower_id'))
                        else:
                            # Ignoring other events like 'new_post' and 'new_notification'
                            pass
                        
                        # Processed successfully, update the cursor
                        last_id = message_id
                        set_last_id(last_id)
                        
        except redis.ConnectionError:
            print("Connection to Redis lost. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Error consuming events: {e}")
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nConsumer stopped.")

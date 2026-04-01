import redis
import time

# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

STREAM_KEY = 'system_logs'

def main():
    print(f"Starting cleanup for stream: '{STREAM_KEY}'")
    
    # Calculate timestamp for 1 week ago in milliseconds
    # 1 week = 7 days * 24 hours * 60 minutes * 60 seconds * 1000 milliseconds
    one_week_in_ms = 7 * 24 * 60 * 60 * 1000
    current_time_ms = int(time.time() * 1000)
    
    # Threshold timestamp (ID limit)
    threshold_ms = current_time_ms - one_week_in_ms
    
    print(f"Current Time (ms): {current_time_ms}")
    print(f"Threshold Time (ms): {threshold_ms} (exactly 1 week ago)")
    print(f"Command to be executed: XTRIM {STREAM_KEY} MINID ~ {threshold_ms}\n")

    # The approximate=True option uses the '~' operator, making the 
    # trim slightly less exact but significantly faster for Redis.
    removed_count = redis_client.xtrim(STREAM_KEY, minid=threshold_ms, approximate=True)
    
    print(f"\u2705 Cleanup complete! Removed approximately {removed_count} old log entries.\n")
    print("Tip: You can set up a cron job to run this script automatically every hour/day.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\u274c Error during cleanup: {e}")

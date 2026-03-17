import redis
import time
import uuid

# Connect to local Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def acquire_lock(lock_name, acquire_timeout=10, lock_timeout=10):
    """
    Attempts to acquire a distributed lock.

    :param lock_name: Unique name for the lock.
    :param acquire_timeout: Time to wait for the lock to become available.
    :param lock_timeout: Max time the lock should be held (safety expiration).
    :return: Identifier for the lock if acquired, False otherwise.
    """
    identifier = str(uuid.uuid4())
    lock_key = f"lock:{lock_name}"
    end = time.time() + acquire_timeout

    while time.time() < end:
        # SET with NX (Set if Not eXists) and PX (milliseconds expiration)
        # provides an atomic way to acquire the lock.
        if r.set(lock_key, identifier, nx=True, px=lock_timeout * 1000):
            return identifier
        time.sleep(0.1)

    return False


def release_lock(lock_name, identifier):
    """
    Releases the lock only if the identifier matches (to prevent accidental
    releases by other processes).
    """
    lock_key = f"lock:{lock_name}"

    # Use a Lua script to ensure atomicity: only delete if the value matches
    # This is a standard pattern for Redis distributed locks.
    script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    return r.eval(script, 1, lock_key, identifier)


def simulate_distributed_locks():
    print("--- Simulating Distributed Locks ---")
    lock_name = "process_update"

    # 1. Attempt to acquire lock
    print("Process 1: Attempting to acquire lock...")
    id1 = acquire_lock(lock_name)

    if id1:
        print(f"Process 1: Lock acquired (ID: {id1})")

        # 2. Attempt to acquire same lock (should fail)
        print("Process 2: Attempting to acquire same lock...")
        id2 = acquire_lock(lock_name, acquire_timeout=2)

        if not id2:
            print("Process 2: Failed to acquire lock (already held).")

        # 3. Release lock
        print("Process 1: Releasing lock...")
        if release_lock(lock_name, id1):
            print("Process 1: Lock released successfully.")

        # 4. Try again (should succeed now)
        print("Process 2: Trying again...")
        id2 = acquire_lock(lock_name)
        if id2:
            print(f"Process 2: Lock acquired (ID: {id2})")
            release_lock(lock_name, id2)
            print("Process 2: Lock released.")
    else:
        print("Failed to acquire initial lock.")


if __name__ == "__main__":
    try:
        r.ping()
        simulate_distributed_locks()
    except redis.ConnectionError:
        print("Error: Could not connect to Redis. "
              "Please ensure the Redis server is running.")

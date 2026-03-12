#!/bin/bash

# Ensure Redis is running
docker compose up -d

echo "=== Redis Data Structures Tutorial ==="

echo -e "\n--- 1. HASHES (Objects) ---"
# Hashes are maps between string fields and string values. Perfect for representing objects.
docker compose exec redis redis-cli HSET user:1001 name "John Doe" email "john@example.com" age "30"
# Get a single field
docker compose exec redis redis-cli HGET user:1001 name
# Get all fields and values
docker compose exec redis redis-cli HGETALL user:1001
# Increment a field inside a hash
docker compose exec redis redis-cli HINCRBY user:1001 age 1

echo -e "\n--- 2. LISTS (Queues / Timelines) ---"
# Lists are simple lists of strings, sorted by insertion order.
# LPUSH adds to the head (left), RPUSH to the tail (right)
docker compose exec redis redis-cli LPUSH messages:queue "Task 3"
docker compose exec redis redis-cli LPUSH messages:queue "Task 2"
docker compose exec redis redis-cli LPUSH messages:queue "Task 1"
docker compose exec redis redis-cli RPUSH messages:queue "Task 4"
# Get elements from index 0 to 2
docker compose exec redis redis-cli LRANGE messages:queue 0 2
# LPOP removes and returns the first element (left)
docker compose exec redis redis-cli LPOP messages:queue
# LPOP removes the next one
docker compose exec redis redis-cli LPOP messages:queue

echo -e "\n--- 3. SETS (Unique collections) ---"
# Sets are unordered collections of unique strings. Good for tags, relationships.
docker compose exec redis redis-cli SADD tags:redis "fast" "database" "in-memory" "fast"
# List all elements (notice "fast" is only there once)
docker compose exec redis redis-cli SMEMBERS tags:redis
# Check if an element exists in a set (1 means yes, 0 means no)
docker compose exec redis redis-cli SISMEMBER tags:redis "in-memory"

echo -e "\n--- 4. SORTED SETS (Leaderboards) ---"
# Sorted Sets are like Sets, but every element has an associated floating number called a "score".
docker compose exec redis redis-cli ZADD leaderboard 100 "PlayerA" 50 "PlayerB" 250 "PlayerC"
# Add to a user's score
docker compose exec redis redis-cli ZINCRBY leaderboard 10 "PlayerA"
# Get leaderboard from highest to lowest score with scores
docker compose exec redis redis-cli ZREVRANGE leaderboard 0 -1 WITHSCORES
# Get the rank of a player (0 is highest since we use ZREVRANK)
docker compose exec redis redis-cli ZREVRANK leaderboard "PlayerA"

echo -e "\n--- 5. BITMAPS (Efficient boolean flags) ---"
# Not an actual data type, but bit-level operations on Strings. Great for daily active users.
# User ID 5 logged in on day 1
docker compose exec redis redis-cli SETBIT daily_active_users:2026-03-12 5 1
# User ID 8 logged in on day 1
docker compose exec redis redis-cli SETBIT daily_active_users:2026-03-12 8 1
# Count total active users on that day (Count the 1s)
docker compose exec redis redis-cli BITCOUNT daily_active_users:2026-03-12

echo -e "\n--- 6. HYPERLOGLOG (Approximate Counting) ---"
# Probabilistic structure to estimate unique elements using very little memory (12KB max).
docker compose exec redis redis-cli PFADD unique_ips:2026-03-12 "192.168.1.1" "10.0.0.1" "192.168.1.1" "172.16.0.4"
# Count approximate unique IPs (will return 3)
docker compose exec redis redis-cli PFCOUNT unique_ips:2026-03-12

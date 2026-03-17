#!/bin/bash

# Ensure Redis is running
docker compose up -d

echo "--- 1. Basic PUBLISH (No Subscribers) ---"
# PUBLISH returns the number of subscribers that received the message.
# Since no one is listening yet, this will return (integer) 0.
docker compose exec redis redis-cli PUBLISH news "Breaking News: Redis is awesome!"

echo -e "\n--- 2. Pattern Matching with PSUBSCRIBE ---"
echo "Setting up a background listener for the pattern 'user:*'..."

# We start a subscriber in the background and redirect output to a temp file.
# PSUBSCRIBE allows using wildcards like * or ?
LOG_FILE="/tmp/redis_pubsub.log"
> "$LOG_FILE"
docker compose exec redis redis-cli PSUBSCRIBE "user:*" > "$LOG_FILE" 2>&1 &
SUB_PID=$!

# Give the subscriber a moment to establish the connection
sleep 1

echo "Publishing to 'user:123' (Matches pattern)..."
docker compose exec redis redis-cli PUBLISH user:123 "User 123 has logged in"

echo "Publishing to 'user:orders' (Matches pattern)..."
docker compose exec redis redis-cli PUBLISH user:orders "New order #456 created"

echo "Publishing to 'system:alerts' (Does NOT match)..."
docker compose exec redis redis-cli PUBLISH system:alerts "Disk space low"

# Give it a second to process the messages
sleep 1

# Stop the background subscriber
kill $SUB_PID 2>/dev/null

echo -e "\n--- Results Captured by Subscriber ---"
# We'll see the confirmations and only the messages that matched.
cat "$LOG_FILE"

# Cleanup
rm "$LOG_FILE"

echo -e "\n--- 3. Multiple Patterns ---"
echo "You can also subscribe to multiple patterns at once:"
echo "PSUBSCRIBE 'h?llo' 'orders:*'"
echo "(Matches 'hello', 'hallo', 'hxllo', and anything starting with 'orders:')"

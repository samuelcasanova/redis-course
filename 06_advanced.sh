#!/bin/bash

docker compose up -d

echo -e "\n--- 1. Transactions ---"

# We must send all commands to a single redis-cli process so they happen in the same session/connection.
# The -T flag disables TTY allocation, which is necessary when piping input to `docker compose exec`.
docker compose exec -T redis redis-cli <<EOF
MULTI
SET user:1:name "Samuel"
SET user:1:email "samuel@samuel.com"
INCR user:1:visits
EXEC
EOF

# Using WATCH requires checking the value, then running the transaction.
# Since redis-cli doesn't support variables internally, we can fetch the value to Bash first.
VISITS=$(docker compose exec -T redis redis-cli GET user:1:visits | tr -d '\r')
VISITS=${VISITS:-0} # Default to 0 if null

NEW_VISITS=$((VISITS + 10))

# Now we run WATCH, MULTI, and the calculated SET in a single session.
docker compose exec -T redis redis-cli <<EOF
WATCH user:1:visits
MULTI
SET user:1:visits $NEW_VISITS
EXEC
EOF

echo -e "\n--- 2. Lua Scripting (Rate Limit) ---"
# Short Lua script for sliding window rate limiting (max 5 reqs / 10s)
LUA_SCRIPT="
local k=KEYS[1]
local lim=tonumber(ARGV[1])
local win=tonumber(ARGV[2])
local now=tonumber(ARGV[3])
local id=ARGV[4]

redis.call('ZREMRANGEBYSCORE', k, '-inf', now - win)
if redis.call('ZCARD', k) < lim then
  redis.call('ZADD', k, now, id)
  redis.call('EXPIRE', k, win)
  return 1
else return 0 end
"
# Execute the script
docker compose exec -T redis redis-cli EVAL "$LUA_SCRIPT" 1 rate:user:1 5 10 $(date +%s) $RANDOM

echo -e "\n--- 3. Monitoring ---"
docker compose exec -T redis redis-cli INFO
docker compose exec -T redis redis-cli SLOWLOG GET 10 # To get the slow commands
# This is a blocking command to monitor the executed commands in real time -> docker compose exec -T redis redis-cli MONITOR
docker compose exec -T redis redis-cli SET sample:1:key 1000000000000000000
docker compose exec -T redis redis-cli MEMORY USAGE sample:1:key

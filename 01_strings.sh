#!/bin/bash

docker compose up -d

echo "--- 1. SET and GET ---"
# SET stores a string value.
docker compose exec redis redis-cli SET greeting "Hello, Redis!"
# GET retrieves the string value.
docker compose exec redis redis-cli GET greeting

echo -e "\n--- 2. MSET and MGET (Multiple Set/Get) ---"
# MSET sets multiple keys to multiple values.
docker compose exec redis redis-cli MSET user:1000:name "Alice" user:1000:email "alice@example.com"
# MGET gets the values of all the given keys.
docker compose exec redis redis-cli MGET user:1000:name user:1000:email

echo -e "\n--- 3. Numerical Operations (Counters) ---"
# Redis strings can be used as counters if they contain integers.
docker compose exec redis redis-cli SET page_views 100
# INCR increments the number stored at key by one.
docker compose exec redis redis-cli INCR page_views
# INCRBY increments the number stored at key by the specified integer.
docker compose exec redis redis-cli INCRBY page_views 50
# DECR decrements the number stored at key by one.
docker compose exec redis redis-cli DECR page_views
# DECRBY decrements the number stored at key by the specified integer.
docker compose exec redis redis-cli DECRBY page_views 10

echo -e "\n--- 4. APPEND ---"
# APPEND appends the string representation of the value at the end of the string.
docker compose exec redis redis-cli SET my_string "Hello"
docker compose exec redis redis-cli APPEND my_string " World"
docker compose exec redis redis-cli GET my_string

echo -e "\n--- 5. STRLEN ---"
# STRLEN returns the length of the string value stored at key.
docker compose exec redis redis-cli STRLEN my_string

echo -e "\n--- 6. GETSET ---"
# GETSET atomically sets key to value and returns the old value stored at key.
docker compose exec redis redis-cli GETSET greeting "Hola, Redis!"
docker compose exec redis redis-cli GET greeting

echo -e "\n--- 7. Expiration (SETEX) ---"
# SETEX sets the value and expiration time (in seconds) in a single command.
docker compose exec redis redis-cli SETEX temporary_key 10 "Value that expires in 10 seconds"
# TTL returns the remaining time to live of a key that has a timeout.
docker compose exec redis redis-cli TTL temporary_key
# EXPIRE updates the TTL of a key
docker compose exec redis redis-cli EXPIRE temporary_key 20


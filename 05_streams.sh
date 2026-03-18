#!/bin/bash

docker compose up -d

echo -e "\n--- 1. XADD (Add Entry to Stream) ---"
FIRST_ID=$(docker compose exec redis redis-cli XADD race:france "*" rider Castilla speed 30.2 position 1 location_id 1)
echo "First ID: $FIRST_ID"
docker compose exec redis redis-cli XADD race:france "*" rider Norem speed 28.8 position 3 location_id 1
LAST_ID=$(docker compose exec redis redis-cli XADD race:france "*" rider Prickett speed 29.7 position 2 location_id 1)
echo "Last ID: $LAST_ID"

echo -e "\n--- 2. XRANGE (Read the full range of Entries with count) ---"
# We use '-' (minimum possible ID) and '+' (maximum possible ID).
docker compose exec redis redis-cli XRANGE race:france - + COUNT 2

echo -e "\n--- 3. XRANGE with captured IDs ---"
echo "Reading from $FIRST_ID to $LAST_ID excluding the first entry:"
docker compose exec redis redis-cli XRANGE race:france "($FIRST_ID" "$LAST_ID"

echo -e "\n--- 4. XREAD (Read Entries from Stream as the arrive) ---"
# Use XREAD with BLOCK to wait for new entries when you need to consume messages as they arrive, $ means the last stored ID of the stream
docker compose exec redis redis-cli XREAD COUNT 100 BLOCK 300 STREAMS race:france $

echo -e "\n--- 5. XLEN (Count Entries in Stream) ---"
docker compose exec redis redis-cli XLEN race:france

echo -e "\n--- 6. XREVRANGE (Read the full range of Entries in reverse order with count to get the last element in the stream) ---"
docker compose exec redis redis-cli XREVRANGE race:france + - COUNT 1

echo -e "\n--- 7. XDEL (Delete Entries from Stream) ---"
docker compose exec redis redis-cli XDEL race:france $LAST_ID
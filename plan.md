**LEVEL 1 - FUNDAMENTALS (the basics you already know):**

- Strings (GET/SET/DEL)
- Key expiration (TTL, EXPIRE)
- Redis as a distributed cache
- Basic configuration (RDB/AOF persistence)

**LEVEL 2 - DATA STRUCTURES:**

- **Hashes** - storing objects (user:{id} with fields name, email, etc.)
- **Lists** - FIFO/LIFO queues (LPUSH/RPUSH/LPOP/RPOP)
- **Sets** - unique collections (tags, followers)
- **Sorted Sets** - leaderboards, rankings with scores
- **Bitmaps** - efficient tracking (daily active users)
- **HyperLogLog** - approximate counting of unique elements (unique visitors)

**LEVEL 3 - COMMON USAGE PATTERNS:**

- **Rate limiting** - limiting requests per user/IP
- **Session storage** - distributed user sessions
- **Distributed locks** - synchronization between services (Redlock pattern)
- **Leaderboards** - with sorted sets
- **Cache patterns** - cache-aside, write-through, write-behind
- **Cache invalidation** - strategies to invalidate cache

**LEVEL 4 - PUB/SUB:**

- Channels and pattern matching (`SUBSCRIBE`, `PSUBSCRIBE`)
- Real-time communication between services (e.g., chat, status updates)
- Differences vs message brokers (RabbitMQ/Kafka):
    - **Redis PubSub**: Ephemeral ("fire-and-forget"). No persistence. Fast, simple.
    - **Kafka/RabbitMQ**: Persistent logs, consumer acks, guaranteed delivery.
- When to use Pub/Sub vs Streams:
    - **Pub/Sub**: When latency is key and dropping messages during downtime is acceptable (e.g., UI notifications).
    - **Streams**: When you need message history, consumer groups, and persistence (replayability).

**LEVEL 5 - REDIS STREAMS (the most modern):**

- Event sourcing and event-driven architecture
- Consumer groups (similar to Kafka)
- XADD, XREAD, XREADGROUP
- Use cases: activity feeds, logs, event streaming
- Comparison with Kafka

**LEVEL 6 - ADVANCED:**

- **Transactions** (MULTI/EXEC/WATCH)
- **Lua scripting** - complex atomic operations
- **Pipelining** - multiple commands in batch
- **Redis Cluster** - horizontal sharding and high availability
- **Redis Sentinel** - automatic failover
- **Replication** - master-slave

**LEVEL 7 - MONITORING AND PERFORMANCE:**

- MONITOR, SLOWLOG, INFO
- Memory optimization (encoding, eviction policies)
- Profiling and debugging
- Benchmarking with redis-benchmark

**SUGGESTED PRACTICAL PROJECT:**

Create a system that combines several use cases:

**"Engagement system for a social app":**

- **Cache** - user profiles
    - Cache aside strategy, created a simple cache called users:top with a sorted array of 3 user objects, with a TTL of 60 seconds.
- **Sorted Sets** - trending posts (by likes/views)
    - Created a sorted set called posts:trending with the score being the sum of likes and views. Initialized in the init_db.py script once the posts exists in the DB. Every time a post is liked or viewed, the score is incremented by 1.
- **Sets** - followers/following relationships
    - Created a set called user:user_id:followers with the users that follow the user. Created another set called user:user_id:following with the users that the user is following. Every time a user follows another user, the follower is added to the following set of the followed user and the followed user is added to the followers set of the follower.
- **Lists** - timeline of posts
    - Created a list called timeline:user_id with the posts of the users that the user is following, populated with a fan-out on write strategy. Everytime a post is created the post is added to the timeline of all the followers of the author.
- **Pub/Sub** - real-time notifications
- **Streams** - event log of all actions
- **Rate limiting** - hourly limit of posts
- **Distributed lock** - prevent double-posting
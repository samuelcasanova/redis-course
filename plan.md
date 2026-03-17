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

**LEVEL 4 - PUB/SUB [IN PROGRESS]:**

- Channels and pattern matching
- Real-time communication between services
- Differences vs message brokers (RabbitMQ/Kafka)
- When to use Pub/Sub vs Streams

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
- **Sorted Sets** - trending posts (by likes/views)
- **Sets** - followers/following relationships
- **Lists** - timeline of posts
- **Pub/Sub** - real-time notifications
- **Streams** - event log of all actions
- **Rate limiting** - hourly limit of posts
- **Distributed lock** - prevent double-posting
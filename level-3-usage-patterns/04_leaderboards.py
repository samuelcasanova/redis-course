import redis

# Connect to local Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def increment_score(user_id, score_delta):
    """
    Updates a user's score in the leaderboard.
    """
    r.zincrby("leaderboard:global", score_delta, user_id)


def get_top_players(n=5):
    """
    Retrieves the top N players and their scores.
    """
    return r.zrevrange("leaderboard:global", 0, n - 1, withscores=True)


def get_player_rank(user_id):
    """
    Retrieves the rank of a specific player (1-indexed).
    """
    rank = r.zrevrank("leaderboard:global", user_id)
    if rank is not None:
        return rank + 1
    return None


def simulate_leaderboard():
    print("--- Simulating Leaderboard ---")
    leaderboard_key = "leaderboard:global"
    r.delete(leaderboard_key)

    # 1. Add some initial players
    players = {
        "alice": 1500,
        "bob": 1200,
        "charlie": 1800,
        "david": 900,
        "eve": 2100
    }

    print("Adding initial scores...")
    for player, score in players.items():
        r.zadd(leaderboard_key, {player: score})

    # 2. Show top 3
    print("\nTop 3 Players:")
    top_3 = get_top_players(3)
    for i, (player, score) in enumerate(top_3):
        print(f"{i+1}. {player}: {score}")

    # 3. Update a score
    print("\nbob scores 1000 points!")
    increment_score("bob", 1000)

    # 4. Show new top 3 and specific ranks
    print("\nNew Top 3 Players:")
    new_top_3 = get_top_players(3)
    for i, (player, score) in enumerate(new_top_3):
        print(f"{i+1}. {player}: {score}")

    user = "alice"
    print(f"\n{user}'s current rank: {get_player_rank(user)}")


if __name__ == "__main__":
    try:
        r.ping()
        simulate_leaderboard()
    except redis.ConnectionError:
        print("Error: Could not connect to Redis. "
              "Please ensure the Redis server is running.")

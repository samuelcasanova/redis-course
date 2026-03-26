import { useEffect, useState } from 'react';
import './App.css';

interface User {
  id: number;
  username: string;
  email: string;
  bio: string;
  post_count?: number;
}

interface UserWithFollows extends User {
  followers_count?: number;
  following_count?: number;
}

interface Post {
  id: number;
  title: string;
  text: string;
  timestamp: string;
  likes: number[];
  views: number[];
  author: {
    id: number;
    username: string;
  };
}

interface TrendingPost extends Post {
  score: number;
}

type PostTab = 'latest' | 'trending';

const CONNECTED_USER_ID = 1234;

function App() {
  const [topUsers, setTopUsers] = useState<UserWithFollows[]>([]);
  const [recentPosts, setRecentPosts] = useState<Post[]>([]);
  const [trendingPosts, setTrendingPosts] = useState<TrendingPost[]>([]);
  const [activeTab, setActiveTab] = useState<PostTab>('latest');
  const [trendingLoaded, setTrendingLoaded] = useState(false);

  const [viewingUserId, setViewingUserId] = useState<number | null>(null);
  const [viewingUser, setViewingUser] = useState<UserWithFollows | null>(null);
  const [userFollowers, setUserFollowers] = useState<User[]>([]);
  const [userFollowing, setUserFollowing] = useState<User[]>([]);
  const [mutualFollowing, setMutualFollowing] = useState<User[]>([]);
  const [profileLoading, setProfileLoading] = useState(false);

  useEffect(() => {
    // Fetch Top 3 Users and their follow stats
    fetch('http://localhost:8000/users/top')
      .then(res => res.json())
      .then(async (data: User[]) => {
        // For each user, fetch their followers and following
        const usersWithFollows = await Promise.all(
          data.map(async (user) => {
            try {
              const [followersRes, followingRes] = await Promise.all([
                fetch(`http://localhost:8000/users/${user.id}/followers`),
                fetch(`http://localhost:8000/users/${user.id}/following`)
              ]);
              const followers = await followersRes.json();
              const following = await followingRes.json();
              return {
                ...user,
                followers_count: followers.length || 0,
                following_count: following.length || 0
              };
            } catch (err) {
              console.error(`Failed to fetch follows for user ${user.id}`, err);
              return { ...user, followers_count: 0, following_count: 0 };
            }
          })
        );
        setTopUsers(usersWithFollows);
      })
      .catch(console.error);

    // Fetch Recent Posts (always loaded upfront)
    fetch('http://localhost:8000/posts/recent')
      .then(res => res.json())
      .then(data => setRecentPosts(data))
      .catch(console.error);
  }, []);

  // Lazy-load trending posts only when the tab is first selected
  useEffect(() => {
    if (activeTab === 'trending' && !trendingLoaded) {
      fetch('http://localhost:8000/posts/trending')
        .then(res => res.json())
        .then(data => {
          setTrendingPosts(data);
          setTrendingLoaded(true);
        })
        .catch(console.error);
    }
  }, [activeTab, trendingLoaded]);

  const postsToShow = activeTab === 'latest' ? recentPosts : trendingPosts;

  const openUserProfile = async (userId: number) => {
    setViewingUserId(userId);
    setProfileLoading(true);
    setViewingUser(null);
    try {
      const [profileRes, followersRes, followingRes, mutualRes] = await Promise.all([
        fetch(`http://localhost:8000/users/${userId}`),
        fetch(`http://localhost:8000/users/${userId}/followers`),
        fetch(`http://localhost:8000/users/${userId}/following`),
        fetch(`http://localhost:8000/users/${CONNECTED_USER_ID}/mutual_following/${userId}`)
      ]);
      
      const profileInfo = await profileRes.json();
      const followersData = await followersRes.json();
      const followingData = await followingRes.json();
      const mutualData = await mutualRes.json();

      setViewingUser({
        ...profileInfo,
        followers_count: followersData.length,
        following_count: followingData.length
      });
      setUserFollowers(followersData.slice(0, 50));
      setUserFollowing(followingData.slice(0, 50));
      setMutualFollowing(mutualData);
    } catch (err) {
      console.error(err);
    } finally {
      setProfileLoading(false);
    }
  };

  if (viewingUserId) {
    return (
      <div className="app-container">
        <main className="dashboard-layout">
          <header className="dashboard-header">
            <div className="header-badges">
              <button onClick={() => setViewingUserId(null)} className="back-btn">
                 ← Go to Home Page
              </button>
            </div>
            <h1 className="app-title clickable-title" onClick={() => setViewingUserId(null)}>
              {viewingUser ? `${viewingUser.username}'s Profile` : 'Loading...'}
            </h1>
          </header>

          {profileLoading || !viewingUser ? (
            <p className="posts-empty">Loading profile data...</p>
          ) : (
            <div className="dashboard-grid">
              <section className="dashboard-section">
                <h2>Profile Info</h2>
                <div style={{ marginBottom: "1rem" }}>
                  <p className="user-email">{viewingUser.email}</p>
                  <p className="user-bio">{viewingUser.bio}</p>
                  <div className="user-follow-stats" style={{ marginTop: "1rem" }}>
                    <span className="stat-pill">{viewingUser.followers_count} Followers</span>
                    <span className="stat-pill">{viewingUser.following_count} Following</span>
                  </div>
                </div>

                {viewingUser.id !== CONNECTED_USER_ID && (
                  <div className="mutual-connections">
                    <h3>🌟 Mutual Connections ({mutualFollowing.length})</h3>
                    <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                      Users that both you and @{viewingUser.username} follow.
                    </p>
                    <div className="user-chips">
                      {mutualFollowing.length > 0 ? (
                        mutualFollowing.map(u => (
                          <span key={u.id} className="user-chip" onClick={() => openUserProfile(u.id)}>
                            @{u.username}
                          </span>
                        ))
                      ) : (
                        <span style={{color: "var(--text-secondary)", fontSize: "0.85rem"}}>No mutual connections</span>
                      )}
                    </div>
                  </div>
                )}
              </section>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                <section className="dashboard-section">
                  <h2>Followers ({viewingUser.followers_count})</h2>
                  <div className="user-chips">
                    {userFollowers.length > 0 ? userFollowers.map(u => (
                      <span key={u.id} className="user-chip" onClick={() => openUserProfile(u.id)}>
                        @{u.username}
                      </span>
                    )) : <span style={{color: "var(--text-secondary)", fontSize: "0.85rem"}}>No followers yet</span>}
                  </div>
                </section>

                <section className="dashboard-section">
                  <h2>Following ({viewingUser.following_count})</h2>
                  <div className="user-chips">
                    {userFollowing.length > 0 ? userFollowing.map(u => (
                      <span key={u.id} className="user-chip" onClick={() => openUserProfile(u.id)}>
                        @{u.username}
                      </span>
                    )) : <span style={{color: "var(--text-secondary)", fontSize: "0.85rem"}}>Not following anyone</span>}
                  </div>
                </section>
              </div>
            </div>
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="app-container">
      <main className="dashboard-layout">
        <header className="dashboard-header">
          <div className="header-badges">
            <div className="app-badge">Pre-Alpha Skeleton</div>
            <div className="logged-in-badge">👤 Logged in as User #1234</div>
          </div>
          <h1 className="app-title clickable-title" onClick={() => setViewingUserId(null)}>Engagement System</h1>
        </header>
        
        <div className="dashboard-grid">
          {/* Posts Section */}
          <section className="dashboard-section posts-section">
            {/* Tab switcher */}
            <div className="posts-tabs">
              <button
                id="tab-latest"
                className={`posts-tab${activeTab === 'latest' ? ' active' : ''}`}
                onClick={() => setActiveTab('latest')}
              >
                📰 Latest
              </button>
              <button
                id="tab-trending"
                className={`posts-tab${activeTab === 'trending' ? ' active' : ''}`}
                onClick={() => setActiveTab('trending')}
              >
                🔥 Trending
              </button>
            </div>

            <div className="posts-list">
              {postsToShow.length === 0 ? (
                <p className="posts-empty">Loading posts…</p>
              ) : (
                postsToShow.map(post => (
                  <article key={post.id} className="post-card">
                    <div className="post-header">
                      <span 
                        className="post-author clickable-user" 
                        onClick={() => openUserProfile(post.author.id)}
                      >
                        @{post.author.username}
                      </span>
                      <div className="post-header-right">
                        {activeTab === 'trending' && (
                          <span className="score-badge">🔥 {(post as TrendingPost).score}</span>
                        )}
                        <span className="post-time">{new Date(post.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                    <h3 className="post-title">{post.title}</h3>
                    <p className="post-text">{post.text}</p>
                    <div className="post-footer">
                      <span>👍 {post.likes.length} Likes</span>
                      <span>👁️ {post.views.length} Views</span>
                    </div>
                  </article>
                ))
              )}
            </div>
          </section>

          {/* Top Authors Section */}
          <section className="dashboard-section authors-section">
            <h2>Top Authors</h2>
            <div className="users-list">
              {topUsers.map(user => (
                <div 
                  key={user.id} 
                  className="user-card clickable-user"
                  onClick={() => openUserProfile(user.id)}
                >
                  <div className="user-card-header">
                    <h3>{user.username}</h3>
                    <div className="post-count-badge">{user.post_count} Posts</div>
                  </div>
                  <p className="user-email">{user.email}</p>
                  <p className="user-bio">{user.bio}</p>
                  <div className="user-follow-stats">
                    <span className="stat-pill">{user.followers_count} Followers</span>
                    <span className="stat-pill">{user.following_count} Following</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;

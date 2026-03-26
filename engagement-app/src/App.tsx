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

function App() {
  const [topUsers, setTopUsers] = useState<UserWithFollows[]>([]);
  const [recentPosts, setRecentPosts] = useState<Post[]>([]);
  const [trendingPosts, setTrendingPosts] = useState<TrendingPost[]>([]);
  const [activeTab, setActiveTab] = useState<PostTab>('latest');
  const [trendingLoaded, setTrendingLoaded] = useState(false);

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

  return (
    <div className="app-container">
      <main className="dashboard-layout">
        <header className="dashboard-header">
          <div className="app-badge">Pre-Alpha Skeleton</div>
          <h1 className="app-title">Engagement System</h1>
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
                      <span className="post-author">@{post.author.username}</span>
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
                <div key={user.id} className="user-card">
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

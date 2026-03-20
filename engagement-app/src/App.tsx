import { useEffect, useState } from 'react';
import './App.css';

interface User {
  id: number;
  username: string;
  email: string;
  bio: string;
}

function App() {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/users')
      .then(res => res.json())
      .then(data => setUsers(data))
      .catch(err => console.error("Failed to fetch users", err));
  }, []);
  return (
    <div className="app-container">
      <main className="skeleton-card">
        <div className="app-badge">Pre-Alpha Skeleton</div>
        <h1 className="app-title">Engagement System</h1>
        <div className="users-list">
          {users.map(user => (
            <div key={user.id} className="user-card">
              <h3>{user.username}</h3>
              <p className="user-email">{user.email}</p>
              <p className="user-bio">{user.bio}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

export default App;

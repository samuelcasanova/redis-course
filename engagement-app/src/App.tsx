import './App.css';

function App() {
  return (
    <div className="app-container">
      <main className="skeleton-card">
        <div className="app-badge">Pre-Alpha Skeleton</div>
        <h1 className="app-title">Engagement System</h1>
        <p className="hello-message">
          Hello World! The foundation is ready. This is where the real-time social app magic will happen.
        </p>
        
        <button 
          className="interactive-button"
          onClick={() => console.log('Welcome to the Skeleton!')}
        >
          Explore Future Ideas
        </button>
      </main>
    </div>
  );
}

export default App;

import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [visibleChars, setVisibleChars] = useState(0);
  const [showCursor, setShowCursor] = useState(true);
  const [animationComplete, setAnimationComplete] = useState(false);
  
  const text = "I've seent it";

  useEffect(() => {
    // Start typewriter effect after brief delay
    const startDelay = setTimeout(() => {
      const typewriterTimer = setInterval(() => {
        setVisibleChars(prev => {
          if (prev < text.length) {
            return prev + 1;
          } else {
            clearInterval(typewriterTimer);
            // Hide cursor after typing is complete
            setTimeout(() => {
              setShowCursor(false);
              setAnimationComplete(true);
            }, 1000);
            return prev;
          }
        });
      }, 150); // 150ms per character for dramatic effect

      return () => clearInterval(typewriterTimer);
    }, 800); // Initial delay before typing starts

    // API call
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        setHealth(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('API Error:', err);
        setLoading(false);
      });

    return () => clearTimeout(startDelay);
  }, [text.length]);

  return (
    <>      
      <div className="hero-section">
        <h1 className={`typewriter-text ${animationComplete ? 'glow-effect' : ''}`}>
          {text.slice(0, visibleChars)}
          {showCursor && <span className="cursor">|</span>}
        </h1>
        
        <div className={`subtitle ${animationComplete ? 'subtitle-fade-in' : ''}`}>
          The beautiful game, analyzed
        </div>
      </div>
      
      <div className={`card ${animationComplete ? 'card-fade-in' : ''}`}>
        {loading ? (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Connecting to the pitch...</p>
          </div>
        ) : health ? (
          <div className="api-status success">
            <p>⚽ Connected to United App API</p>
            <div className="status-details">
              <span>Status: {health.status}</span>
              <span>Port: {health.port}</span>
            </div>
          </div>
        ) : (
          <div className="api-status error">
            <p>❌ Connection failed</p>
            <p>Unable to reach the server</p>
          </div>
        )}
      </div>
    </>
  )
}

export default App
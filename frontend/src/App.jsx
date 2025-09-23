import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        setHealth(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('API Error:', err)
        setLoading(false)
      })
  }, [])

  return (
    <>      
      <p>I've seent it with Vite + React!</p>
      
      <div className="card">
        {loading ? (
          <p>Loading API...</p>
        ) : health ? (
          <div>
            <p>✅ API Connected!</p>
            <p>Status: {health.status}</p>
            <p>Message: {health.message}</p>
            <p>Port: {health.port}</p>
          </div>
        ) : (
          <p>❌ API Connection Failed</p>
        )}
      </div>
    </>
  )
}

export default App
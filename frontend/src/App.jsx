import { useState } from 'react'
import { NavLink, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { getToken, getUsername, logout } from './api.js'
import Login from './pages/Login.jsx'
import Documents from './pages/Documents.jsx'
import Workspace from './pages/Workspace.jsx'
import Quiz from './pages/Quiz.jsx'
import './App.css'

// shows the page only when the student is logged in; otherwise goes to /login
function RequireAuth({ children }) {
  return getToken() ? children : <Navigate to="/login" replace />
}

export default function App() {
  const navigate = useNavigate()
  const [username, setUsername] = useState(getUsername())

  function handleLogout() {
    logout()
    setUsername(null)
    navigate('/login')
  }

  return (
    <div className="app">
      <header className="navbar">
        <h1 className="logo">AI Study Assistant</h1>
        {username && (
          <nav>
            <NavLink to="/documents">My Documents</NavLink>
            <span className="user">{username}</span>
            <button className="btn-link" onClick={handleLogout}>Log out</button>
          </nav>
        )}
      </header>

      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/documents" replace />} />
          <Route path="/login" element={<Login onLogin={setUsername} />} />
          <Route path="/documents" element={<RequireAuth><Documents /></RequireAuth>} />
          <Route path="/workspace/:documentId" element={<RequireAuth><Workspace /></RequireAuth>} />
          <Route path="/quiz/:documentId" element={<RequireAuth><Quiz /></RequireAuth>} />
        </Routes>
      </main>
    </div>
  )
}
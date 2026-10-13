import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../api.js'

export default function Login({ onLogin }) {
  const navigate = useNavigate()
  const [mode, setMode] = useState('login') // 'login' or 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault() // stops the browser from reloading the page
    setError('')

    if (!username.trim()) {
      setError('Please enter a username.')
      return
    }
    if (mode === 'register' && password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setBusy(true)
    try {
      const data =
        mode === 'register'
          ? await register(username.trim(), password)
          : await login(username.trim(), password)
      onLogin(data.username)
      navigate('/documents')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="auth-card">
      <h2>{mode === 'login' ? 'Log in' : 'Create an account'}</h2>

      <form onSubmit={handleSubmit}>
        <label className="field">
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
        </label>

        <label className="field">
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          />
        </label>

        {error && <p className="error">{error}</p>}

        <button className="btn-primary" type="submit" disabled={busy}>
          {busy ? 'Please wait...' : mode === 'login' ? 'Log in' : 'Register'}
        </button>
      </form>

      <p className="switch">
        {mode === 'login' ? 'New here? ' : 'Already have an account? '}
        <button type="button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>
          {mode === 'login' ? 'Create an account' : 'Log in'}
        </button>
      </p>
    </section>
  )
}
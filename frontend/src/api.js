import {
  mockDocuments,
  mockChapters,
  mockAnswer,
  mockNotFound,
  mockLlmDown,
  mockQuizStart,
  mockQuizAnswerKey,
} from './mockData.js'

// true = use fake data, false = call the real backend
const USE_MOCK = true
const API_BASE = '/api'

const TOKEN_KEY = 'study_token'
const USER_KEY = 'study_username'

// same rules as the backend
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt']
const MAX_SIZE = 25 * 1024 * 1024 // 25 MB
const AI_BUSY = 'The AI is busy. Please try again in a minute.'

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// ---------- login state (kept in the browser's localStorage) ----------

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const getUsername = () => localStorage.getItem(USER_KEY)

function saveLogin(data) {
  localStorage.setItem(TOKEN_KEY, data.token)
  localStorage.setItem(USER_KEY, data.username)
  return data
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

// ---------- one function that sends every request ----------

// needsAuth = false only for register and login
async function request(path, options = {}, needsAuth = true) {
  const headers = { ...options.headers }
  if (needsAuth && getToken()) headers.Authorization = `Token ${getToken()}`

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })

  // not logged in, or the token is no longer valid
  if (res.status === 401 && needsAuth) {
    logout()
    window.location.href = '/login'
    throw new Error('Please log in again.')
  }

  if (!res.ok) {
    let data = {}
    try {
      data = await res.json()
    } catch {
      // the error body was not JSON, so keep the default message
    }
    if (res.status === 502 || data.error === 'llm_unavailable') throw new Error(AI_BUSY)

    // Django validation errors look like {"file": ["message"]} or {"detail": "message"}
    const first = Object.values(data)[0]
    const message = Array.isArray(first) ? first[0] : data.detail || data.error || `Request failed (${res.status})`
    throw new Error(message)
  }

  if (res.status === 204) return null
  return res.json()
}

const jsonBody = (body) => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

// ---------- login and register ----------

export async function register(username, password) {
  if (USE_MOCK) {
    await wait(400)
    if (password.length < 8) throw new Error('Password must be at least 8 characters.')
    return saveLogin({ token: 'mock-token', username })
  }
  return saveLogin(await request('/auth/register/', jsonBody({ username, password }), false))
}

export async function login(username, password) {
  if (USE_MOCK) {
    await wait(400)
    if (password === 'wrongpass') throw new Error('Invalid username or password.') // test the error message
    return saveLogin({ token: 'mock-token', username })
  }
  return saveLogin(await request('/auth/login/', jsonBody({ username, password }), false))
}

// ---------- documents (mock store lives in memory only) ----------

// readyAt = the time when a "processing" document becomes "ready"
let mockDocs = mockDocuments.map((d) => ({
  ...d,
  readyAt: d.status === 'processing' ? Date.now() + 8000 : null,
}))

function currentMockDocs() {
  return mockDocs.map((d) =>
    d.readyAt && Date.now() >= d.readyAt ? { ...d, status: 'ready', pages: 12, chunks: 30 } : d,
  )
}

export async function getDocuments() {
  if (USE_MOCK) {
    await wait(300)
    return currentMockDocs()
  }
  return request('/documents/')
}

export async function uploadDocument(file) {
  if (USE_MOCK) {
    await wait(500)
    const dot = file.name.lastIndexOf('.')
    const ext = dot === -1 ? '' : file.name.slice(dot).toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) throw new Error('Only PDF, DOCX and TXT files are allowed.')
    if (file.size > MAX_SIZE) throw new Error('File is too large (max 25 MB).')

    const doc = {
      id: Date.now(),
      title: file.name,
      file: '',
      status: 'processing',
      warnings: [],
      pages: 0,
      chunks: 0,
      created_at: new Date().toISOString(),
      readyAt: Date.now() + 6000,
    }
    mockDocs = [doc, ...mockDocs]
    return doc
  }
  const formData = new FormData()
  formData.append('file', file)
  return request('/documents/', { method: 'POST', body: formData })
}

export async function deleteDocument(id) {
  if (USE_MOCK) {
    await wait(200)
    mockDocs = mockDocs.filter((d) => d.id !== id)
    return null
  }
  return request(`/documents/${id}/`, { method: 'DELETE' })
}

// the real backend returns {"chapters": [...]}; this function returns just the list
export async function getChapters(documentId) {
  if (USE_MOCK) {
    await wait(200)
    return mockChapters
  }
  const data = await request(`/documents/${documentId}/chapters/`)
  return data.chapters
}

// ---------- chat ----------

export async function askQuestion(documentId, question) {
  if (USE_MOCK) {
    await wait(600)
    const q = question.toLowerCase()
    if (q.includes('unknown')) return mockNotFound // type "unknown" to test "not found"
    if (q.includes('busy')) return mockLlmDown // type "busy" to test the AI-busy message
    return mockAnswer
  }
  return request('/chat/', jsonBody({ document_id: documentId, question }))
}

// ---------- quiz ----------

const mockSubmitted = {} // attempt id -> the answers the student sent

// options: { question_type, difficulty, count, chapter }
export async function startQuiz(documentId, options) {
  if (USE_MOCK) {
    await wait(1500) // real generation is slow, so the loader needs testing
    return mockQuizStart
  }
  return request('/quiz/start/', jsonBody({ document_id: documentId, ...options }))
}

// answers looks like {"0": 2, "1": 0} (question index -> chosen option, counted from 0)
export async function submitQuiz(attemptId, answers) {
  if (USE_MOCK) {
    await wait(400)
    mockSubmitted[attemptId] = answers
    const mcqs = mockQuizStart.questions.filter((q) => q.type === 'mcq')
    const score = mcqs.filter((q) => answers[String(q.index)] === mockQuizAnswerKey[q.index].correct_index).length
    return { score, total: mcqs.length }
  }
  return request(`/quiz/${attemptId}/submit/`, jsonBody({ answers }))
}

// NOTE: the exact shape of the real review response is not confirmed yet.
// Check /api/docs/ or backend/README.md before relying on it.
export async function getReview(attemptId) {
  if (USE_MOCK) {
    await wait(300)
    const answers = mockSubmitted[attemptId] || {}
    const questions = mockQuizStart.questions.map((q) => {
      const key = mockQuizAnswerKey[q.index]
      if (q.type !== 'mcq') return { ...q, ...key }
      const selected = answers[String(q.index)] ?? null
      return { ...q, ...key, selected_index: selected, is_correct: selected === key.correct_index }
    })
    return { attempt_id: attemptId, questions }
  }
  return request(`/quiz/${attemptId}/review/`)
}

// NOTE: the shape of the attempts list is not confirmed yet either.
export async function getAttempts(documentId) {
  if (USE_MOCK) {
    await wait(200)
    return []
  }
  const query = documentId ? `?document_id=${documentId}` : ''
  return request(`/quiz/attempts/${query}`)
}
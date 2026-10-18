import {
  mockDocuments,
  mockChapters,
  mockAnswer,
  mockNotFound,
  mockLlmDown,
  mockSummary,
  mockStudyGuide,
  mockQuizStart,
  mockQuizAnswerKey,
} from './mockData.js'
import { clearChats } from './utils/chatStore.js'
import { clearGuides } from './utils/guideStore.js'
import { clearQuizStorage } from './utils/quizStorage.js'

// true  = sample data (demo mode): uploaded files are NOT read and every answer is a fixed example
// false = the real backend and AI service
const USE_MOCK = false;
export const USING_MOCK = USE_MOCK

const API_BASE = '/api'

// PROPOSED address of the revision guide. Zainab has not confirmed it yet.
const STUDY_GUIDE_PATH = '/study-guide/'

// chat and quiz generation can take 60 s or more, so we wait up to 2 minutes
const REQUEST_TIMEOUT_MS = 120000

const TOKEN_KEY = 'study_token'
const USER_KEY = 'study_username'

// same rules as the backend
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt']
const MAX_SIZE = 25 * 1024 * 1024 // 25 MB
const AI_BUSY = 'The AI is busy. Please try again in a minute.'

// the backend can send {"error": "<code>"}, so every code gets a readable message
const ERROR_MESSAGES = {
  llm_unavailable: AI_BUSY,
  chapter_not_found: 'Chapter not found. Choose another chapter, or "All chapters".',
  no_content: 'There is no content to make questions from.',
  ai_failed: AI_BUSY,
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// ---------- login state (kept in the browser's localStorage) ----------

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const getUsername = () => localStorage.getItem(USER_KEY)

function saveLogin(data) {
  localStorage.setItem(TOKEN_KEY, data.token)
  localStorage.setItem(USER_KEY, data.username)
  return data
}

// logging out also clears the quizzes, chats and guides, so the next account never sees them
export function logout() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  clearQuizStorage()
  clearChats()
  clearGuides()
}

// ---------- one function that sends every request ----------

// needsAuth = false only for register and login
async function request(path, options = {}, needsAuth = true) {
  const headers = { ...options.headers }
  if (needsAuth && getToken()) headers.Authorization = `Token ${getToken()}`

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  let res
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers, signal: controller.signal })
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('The request took too long. Please try again.', { cause: err })
    }
    throw new Error('Cannot reach the server. Check that the backend is running.', { cause: err })
  } finally {
    clearTimeout(timer)
  }

  // not logged in, or the token is no longer valid
  if (res.status === 401 && needsAuth) {
    logout()
    window.location.href = '/login'
    throw new Error('Please log in again.')
  }

  if (!res.ok) {
    let data = {}
    try {
      data = (await res.json()) || {}
    } catch {
      // the error body was not JSON, so we use a default message
    }

    let message
    if (ERROR_MESSAGES[data.error]) {
      message = ERROR_MESSAGES[data.error]
    } else if (res.status === 502) {
      // a 502 without an error code comes from the dev proxy, so the backend is not running
      message = 'Cannot reach the server. Check that the backend is running.'
    } else if (res.status === 403) {
      message = data.detail || 'You do not have permission to do this.'
    } else if (res.status === 404) {
      message = 'Not found. It may have been deleted, or it belongs to another account.'
    } else if (res.status === 422) {
      const why = Array.isArray(data.warnings) && data.warnings.length ? ` ${data.warnings[0]}` : ''
      message = (data.detail || 'No questions could be created. Try another chapter, or fewer questions.') + why
    } else if (res.status === 409) {
      message = data.detail || 'The document is not ready yet, or the quiz was already submitted.'
    } else {
      // Django validation errors look like {"file": ["message"]} or {"detail": "message"}
      const first = Object.values(data)[0]
      message = Array.isArray(first) ? first[0] : data.detail || data.error || `Request failed (${res.status})`
    }

    const error = new Error(message)
    error.status = res.status
    throw error
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
  return request('/documents/').then((data) => (Array.isArray(data) ? data : data.results || []))
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

// ---------- revision guide ----------

// NOTE: this endpoint does not exist yet. Until Zainab and Maria confirm it,
// the real call shows "not available on the server yet".
export async function getStudyGuide(documentId) {
  if (USE_MOCK) {
    await wait(1800)
    return mockStudyGuide
  }
  try {
    return await request(STUDY_GUIDE_PATH, jsonBody({ document_id: documentId }))
  } catch (err) {
    if (err.status === 404 || err.status === 405) {
      throw new Error('The revision guide is not available on the server yet.', { cause: err })
    }
    throw err
  }
}

// ---------- chat ----------

export async function askQuestion(documentId, question) {
  if (USE_MOCK) {
    await wait(600)
    const q = question.toLowerCase()
    if (q.includes('unknown')) return mockNotFound // type "unknown" to test "not found"
    if (q.includes('busy')) return mockLlmDown // type "busy" to test the AI-busy message
    if (q.includes('error')) return { answer: '', found: false, sources: [], error: 'internal_error' } // type "error" for a generic error
    if (q.includes('summar')) return mockSummary // type "summary" to test a summary with bullets
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
    if (options.count === 20) throw new Error(AI_BUSY) // test hook: 20 questions = "AI busy"
    if (options.count === 19) return { error: 'no_content', questions: [], warnings: [] } // test hook: 19 = "no content"
    return mockQuizStart
  }

  const body = {
    document_id: documentId,
    question_type: options.question_type,
    difficulty: options.difficulty,
    count: options.count,
  }
  // when no chapter is chosen, the chapter field is left out completely
  if (options.chapter) body.chapter = options.chapter
  return request('/quiz/start/', jsonBody(body))
}

// the same options as startQuiz, but the questions come back already solved
// (correct answers, explanations, sources) and no quiz attempt is created
export async function generateQuestions(documentId, options) {
  if (USE_MOCK) {
    await wait(1200)
    if (options.count === 20) throw new Error(AI_BUSY) // test hook: 20 questions = "AI busy"
    if (options.count === 19) return { error: 'no_content', questions: [], warnings: [] } // test hook: 19 = "no content"
    const solved = mockQuizStart.questions
      .filter((q) => options.question_type === 'mixed' || q.type === options.question_type)
      .map((q) => ({ ...q, ...mockQuizAnswerKey[q.index] }))
      .slice(0, options.count)
    return { questions: solved, warnings: [] }
  }

  const body = {
    document_id: documentId,
    question_type: options.question_type,
    difficulty: options.difficulty,
    count: options.count,
  }
  // when no chapter is chosen, the chapter field is left out completely
  if (options.chapter) body.chapter = options.chapter
  return request('/quiz/generate/', jsonBody(body))
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
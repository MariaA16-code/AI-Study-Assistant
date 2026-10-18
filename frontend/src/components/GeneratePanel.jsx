import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { generateQuestions, getChapters, startQuiz } from '../api.js'
import { saveQuiz } from '../utils/quizStorage.js'
import AnswerCard from './AnswerCard.jsx'
import Spinner from './Spinner.jsx'

const TYPES = [
  { value: 'mcq', label: 'Multiple Choice Questions (MCQs)' },
  { value: 'short', label: 'Short Questions' },
  { value: 'long', label: 'Long Questions' },
  { value: 'mixed', label: 'Mixed Practice' },
  { value: 'quiz', label: 'Create Quiz' },
]

const LEVELS = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
]

const ERROR_TEXT = {
  llm_unavailable: 'The AI is busy. Please try again in a minute.',
  chapter_not_found: 'Chapter not found. Choose another chapter, or "All chapters".',
  no_content: 'There is no content to make questions from.',
}


// extra requests to make when some questions are rejected or a request fails
const MAX_RETRIES = 2

// pause helper: the free AI plan has a rate limit, so requests are spaced out
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// Split a mixed set into mcq / short / long so every type is really requested.
// 1 question: mcq. 2 questions: mcq + short. 3 or more: all three types.
// Long is listed first because it is the heaviest request for the AI.
function splitMixed(n) {
  if (n <= 1) return [['mcq', n]]
  if (n === 2) return [['mcq', 1], ['short', 1]]
  const long = Math.max(1, Math.round(n * 0.2))
  const short = Math.max(1, Math.round(n * 0.3))
  const mcq = n - long - short
  return [['long', long], ['short', short], ['mcq', mcq]].filter(([, k]) => k > 0)
}

// Ask the existing generate endpoint for `wanted` questions of one type.
// If the backend rejects some or a request fails, wait and ask again for the missing ones.
async function fetchOfType(docId, body, type, wanted) {
  let got = []
  const notes = []
  let errorCode = ''
  let tries = 0

  while (got.length < wanted && tries <= MAX_RETRIES) {
    tries += 1
    const canRetry = tries <= MAX_RETRIES

    let res
    try {
      res = await generateQuestions(docId, { ...body, question_type: type, count: wanted - got.length })
    } catch (err) {
      notes.push(`${type}: ${err.message}`)
      if (canRetry) await sleep(8000)
      continue
    }

    if (res.error) {
      errorCode = res.error
      notes.push(`${type}: ${res.error}`)
      if (canRetry) await sleep(8000)
      continue
    }

    const seen = new Set(got.map((q) => String(q.question).trim().toLowerCase()))
    const fresh = (Array.isArray(res.questions) ? res.questions : []).filter(
      (q) => !seen.has(String(q.question).trim().toLowerCase())
    )
    got = [...got, ...fresh]
    if (Array.isArray(res.warnings)) notes.push(...res.warnings)
  }

  return { questions: got, notes, errorCode }
}

export default function GeneratePanel({ doc }) {
  const navigate = useNavigate()
  const [chapters, setChapters] = useState([])
  const [chapter, setChapter] = useState('')
  const [questionType, setQuestionType] = useState('mcq')
  const [difficulty, setDifficulty] = useState('medium')
  const [count, setCount] = useState(5)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [solved, setSolved] = useState([]) // questions shown on this page

  // "Create Quiz" is a mode, not a real question type
  const isQuiz = questionType === 'quiz'

  // load the chapter list for the dropdown (optional, so a failure is ignored)
  useEffect(() => {
    getChapters(doc.id)
      .then((list) => setChapters(Array.isArray(list) ? list : []))
      .catch(() => setChapters([]))
  }, [doc.id])

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setNotice('')
    setSolved([])
    setLoading(true)

    // the backend accepts 1 to 20 questions
    const safeCount = Math.min(20, Math.max(1, Number(count) || 1))

    // the backend only accepts mcq, short, long or mixed, so a quiz is sent as "mixed"
    const body = {
      question_type: isQuiz ? 'mixed' : questionType,
      difficulty,
      count: safeCount,
      chapter: chapter || null,
    }

    try {
      if (isQuiz) {
        // quiz mode: start an attempt and open the quiz page
        const result = await startQuiz(doc.id, body)

        if (result.error) {
          setError(ERROR_TEXT[result.error] || 'Could not create the quiz.')
          return
        }
        if (!result.questions || result.questions.length === 0) {
          setError('No questions were created. Try again, or choose different options.')
          return
        }

        saveQuiz({ ...result, documentId: doc.id, title: doc.title })
        navigate(`/quiz/${result.attempt_id}`)
        return
      }

      // practice modes: one request per type (mixed asks for long, short and mcq separately)
      const plan = questionType === 'mixed' ? splitMixed(safeCount) : [[questionType, safeCount]]

      let list = []
      const notes = []
      let firstCode = ''

      for (const [index, [type, wanted]] of plan.entries()) {
        if (index > 0) await sleep(5000)
        const part = await fetchOfType(doc.id, body, type, wanted)
        list = [...list, ...part.questions]
        notes.push(...part.notes)
        if (part.errorCode && !firstCode) firstCode = part.errorCode
      }

      // keep the usual reading order: mcq first, then short, then long
      const order = { mcq: 0, short: 1, long: 2 }
      list = list
        .map((q, i) => ({ q, i }))
        .sort((a, b) => (order[a.q.type] ?? 3) - (order[b.q.type] ?? 3) || a.i - b.i)
        .map((x) => x.q)

      const why = [...new Set(notes)].join(' | ')

      if (list.length === 0) {
        if (firstCode) setError(ERROR_TEXT[firstCode] || 'Could not create the questions.')
        else setError('No questions were created. ' + (why ? 'Reason: ' + why : 'Try again, or choose different options.'))
        return
      }

      setSolved(list)

      const parts = []
      if (questionType === 'mixed') {
        const counts = { mcq: 0, short: 0, long: 0 }
        list.forEach((q) => { if (counts[q.type] !== undefined) counts[q.type] += 1 })
        parts.push(`Mixed set: ${counts.mcq} MCQ, ${counts.short} short, ${counts.long} long.`)
      }
      if (list.length < safeCount) {
        parts.push(`Only ${list.length} of ${safeCount} questions passed the quality check.`)
        if (why) parts.push('Backend notes: ' + why)
      }
      if (parts.length) setNotice(parts.join(' '))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="panel gen-form">
        <h3 className="panel-title">Generate questions</h3>
        <p className="hint">
          {isQuiz
            ? 'Quiz mode: you answer first, and the correct answers appear after you submit.'
            : 'Questions are made from this document only, with the chapter and page shown as the source.'}
        </p>

        <form onSubmit={handleSubmit}>
          <fieldset disabled={loading}>
            <div className="gen-grid">
              <label className="field wide">
                Chapter
                <select value={chapter} onChange={(e) => setChapter(e.target.value)}>
                  <option value="">All chapters</option>
                  {chapters.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </label>

              <label className="field">
                Question type
                <select value={questionType} onChange={(e) => setQuestionType(e.target.value)}>
                  {TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </label>

              <label className="field">
                Difficulty
                <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                  {LEVELS.map((l) => (
                    <option key={l.value} value={l.value}>{l.label}</option>
                  ))}
                </select>
              </label>

              <label className="field">
                Number of questions (1 to 20)
                <input type="number" min="1" max="20" value={count} onChange={(e) => setCount(e.target.value)} />
              </label>
            </div>
          </fieldset>

          {error && <p className="error">{error}</p>}
          {notice && <p className="hint">{notice}</p>}

          {loading ? (
            <div className="generating">
              <Spinner size={26} />
              <div>
                <strong>{isQuiz ? 'Creating your quiz...' : 'Creating your questions...'}</strong>
                <p>This can take from 10 seconds to a few minutes. Please keep this page open.</p>
              </div>
            </div>
          ) : (
            <button className="btn-primary gen-submit" type="submit">
              {isQuiz ? 'Start quiz' : 'Generate questions'}
            </button>
          )}
        </form>
      </div>

      {solved.length > 0 && (
        <div className="answers">
          <h3 className="panel-title">Practice questions ({solved.length})</h3>
          {solved.map((q, i) => (
            <AnswerCard key={i} question={q} number={i + 1} />
          ))}
        </div>
      )}
    </>
  )
}
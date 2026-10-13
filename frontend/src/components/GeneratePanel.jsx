import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getChapters, startQuiz } from '../api.js'
import { saveQuiz } from '../utils/quizStorage.js'
import Spinner from './Spinner.jsx'

const TYPES = [
  { value: 'mcq', label: 'Multiple choice' },
  { value: 'short', label: 'Short questions' },
  { value: 'long', label: 'Long questions' },
  { value: 'mixed', label: 'Mixed' },
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

export default function GeneratePanel({ doc }) {
  const navigate = useNavigate()
  const [chapters, setChapters] = useState([])
  const [chapter, setChapter] = useState('')
  const [questionType, setQuestionType] = useState('mcq')
  const [difficulty, setDifficulty] = useState('medium')
  const [count, setCount] = useState(5)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // load the chapter list for the dropdown (it is optional, so a failure is ignored)
  useEffect(() => {
    getChapters(doc.id)
      .then((list) => setChapters(Array.isArray(list) ? list : []))
      .catch(() => setChapters([]))
  }, [doc.id])

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setLoading(true)

    // the backend accepts 1 to 20 questions
    const safeCount = Math.min(20, Math.max(1, Number(count) || 1))

    try {
      const result = await startQuiz(doc.id, {
        question_type: questionType,
        difficulty,
        count: safeCount,
        chapter: chapter || null,
      })

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
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel gen-form">
      <h3 className="panel-title">Generate questions</h3>
      <p className="hint">Questions are made from this document only, with the chapter and page shown as the source.</p>

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

        {loading ? (
          <div className="generating">
            <Spinner size={26} />
            <div>
              <strong>Creating your questions...</strong>
              <p>This can take from 10 seconds to a minute. Please keep this page open.</p>
            </div>
          </div>
        ) : (
          <button className="btn-primary gen-submit" type="submit">Generate questions</button>
        )}
      </form>
    </div>
  )
}
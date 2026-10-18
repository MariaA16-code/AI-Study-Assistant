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

      // normal question types: show the questions on this page
      const result = await generateQuestions(doc.id, body)

      if (result.error) {
        setError(ERROR_TEXT[result.error] || 'Could not create the questions.')
        return
      }
      const list = Array.isArray(result.questions) ? result.questions : []
      if (list.length === 0) {
        const why = Array.isArray(result.warnings) ? result.warnings.join(' | ') : ''
        setError('No questions were created. ' + (why ? 'Reason: ' + why : 'Try again, or choose different options.'))
        return
      }

      setSolved(list)
      const warns = Array.isArray(result.warnings) ? result.warnings.join(' | ') : ''
      if (warns) setNotice('Backend notes: ' + warns)
      if (list.length < safeCount) {
        setNotice(`Only ${list.length} of ${safeCount} questions passed the quality check. Try again for more.`)
      }
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
                <p>This can take from 10 seconds to a minute. Please keep this page open.</p>
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


import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { submitQuiz } from '../api.js'
import QuestionCard from '../components/QuestionCard.jsx'
import Spinner from '../components/Spinner.jsx'
import { loadQuiz, saveWritten } from '../utils/quizStorage.js'

export default function Quiz() {
  const { attemptId } = useParams()
  const navigate = useNavigate()
  const [quiz] = useState(() => loadQuiz(attemptId))
  const [choices, setChoices] = useState({}) // question index -> chosen option number
  const [texts, setTexts] = useState({}) // question index -> written answer
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  if (!quiz) {
    return (
      <section>
        <Link className="back-link" to="/documents">← Back to documents</Link>
        <p className="empty">
          This quiz is no longer available. Open a document and use the Generate tab to start a new one.
        </p>
      </section>
    )
  }

  const total = quiz.questions.length
  const answeredCount = quiz.questions.filter((q) =>
    q.type === 'mcq' ? choices[q.index] !== undefined : (texts[q.index] || '').trim() !== '',
  ).length
  const percent = total ? Math.round((answeredCount / total) * 100) : 0
  const gotFewer = quiz.requested && total < quiz.requested
  const warnings = quiz.warnings || []

  const selectOption = (index, option) => setChoices((prev) => ({ ...prev, [index]: option }))
  const changeText = (index, value) => setTexts((prev) => ({ ...prev, [index]: value }))

  async function handleSubmit() {
    if (submitting) return // stops double clicks

    const unanswered = total - answeredCount
    if (unanswered > 0 && !window.confirm(`You have ${unanswered} unanswered question(s). Submit anyway?`)) {
      return
    }

    setSubmitting(true)
    setError('')

    try {
      saveWritten(attemptId, texts)
      // the backend wants {"0": 2, "1": 0}: question index -> chosen option number
      await submitQuiz(attemptId, { ...choices })
      navigate(`/results/${attemptId}`)
    } catch (err) {
      if (err.status === 409) {
        navigate(`/results/${attemptId}`) // this quiz was already submitted
        return
      }
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section>
      <Link className="back-link" to={`/workspace/${quiz.documentId}`}>← Back to workspace</Link>

      <div className="quiz-head">
        <h2>Quiz</h2>
        <p className="hint">{quiz.title} · {total} question{total === 1 ? '' : 's'}</p>
      </div>

      <div className="progress">
        <div className="progress-bar" style={{ width: `${percent}%` }} />
      </div>
      <p className="progress-text">{answeredCount} of {total} answered</p>

      {quiz.questions.map((q, i) => (
        <QuestionCard
          key={q.index}
          question={q}
          number={i + 1}
          selected={choices[q.index]}
          text={texts[q.index] || ''}
          onSelect={selectOption}
          onText={changeText}
        />
      ))}

      {/* a small note under the questions, when fewer questions were created than requested */}
      {(gotFewer || warnings.length > 0) && (
        <div className="quiz-notes">
          {gotFewer && <p className="warning">You asked for {quiz.requested} questions, but only {total} could be created.</p>}
          {warnings.map((w, i) => (
            <p key={i} className="warning">{w}</p>
          ))}
        </div>
      )}

      {error && <p className="error">{error}</p>}

      <div className="submit-bar">
        <p className="hint">Short and long questions are not marked automatically. You will see the model answer after you submit.</p>
        <button className="btn-primary" type="button" onClick={handleSubmit} disabled={submitting}>
          {submitting ? <Spinner size={16} /> : 'Submit quiz'}
        </button>
      </div>
    </section>
  )
}
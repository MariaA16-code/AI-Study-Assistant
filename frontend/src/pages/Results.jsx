import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getReview } from '../api.js'
import ReviewCard from '../components/ReviewCard.jsx'
import Spinner from '../components/Spinner.jsx'
import { loadQuiz, loadWritten } from '../utils/quizStorage.js'

export default function Results() {
  const { attemptId } = useParams()
  const [quiz] = useState(() => loadQuiz(attemptId))
  const [written] = useState(() => loadWritten(attemptId))
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getReview(attemptId)
      .then((data) => setQuestions(Array.isArray(data) ? data : data.questions || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [attemptId])

  const workspaceLink = quiz ? `/workspace/${quiz.documentId}` : '/documents'
  const isPdf = (quiz?.title || '').toLowerCase().endsWith('.pdf')

  // only multiple-choice questions are scored
  const mcqs = questions.filter((q) => q.type === 'mcq')
  const correct = mcqs.filter((q) => q.is_correct).length
  const percent = mcqs.length ? Math.round((correct / mcqs.length) * 100) : 0

  if (loading) {
    return (
      <section>
        <p><Spinner size={18} /> Loading your results...</p>
      </section>
    )
  }

  if (error) {
    return (
      <section>
        <Link className="back-link" to={workspaceLink}>← Back to workspace</Link>
        <p className="error">{error}</p>
      </section>
    )
  }

  return (
    <section>
      <Link className="back-link" to={workspaceLink}>← Back to workspace</Link>
      <h2>Results</h2>
      {quiz && <p className="hint">{quiz.title}</p>}

      <div className="score-card">
        {mcqs.length > 0 ? (
          <>
            <div className="score-ring" style={{ '--pct': `${percent}%` }}>
              <span>{percent}%</span>
            </div>
            <div>
              <h3>{correct} of {mcqs.length} multiple-choice questions correct</h3>
              <p className="hint">
                Short and long questions are not marked automatically. Compare your answers with the model answers below.
              </p>
            </div>
          </>
        ) : (
          <div>
            <h3>This quiz has no multiple-choice questions to score</h3>
            <p className="hint">Compare your answers with the model answers below.</p>
          </div>
        )}
      </div>

      {questions.map((q, i) => (
        <ReviewCard
          key={q.index ?? i}
          question={q}
          number={i + 1}
          writtenAnswer={written[q.index]}
          isPdf={isPdf}
        />
      ))}

      <div className="action-row">
        <Link className="link-btn" to={workspaceLink}>Generate another quiz</Link>
        <Link className="link-btn" to="/documents">My documents</Link>
      </div>
    </section>
  )
}
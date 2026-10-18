import { useState } from 'react'
import { pageLabel } from '../utils/sources.js'

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']
const TYPE_LABELS = { mcq: 'MCQ', short: 'Short', long: 'Long' }

// One practice question on the Generate tab.
// MCQ: the correct option, explanation and source are shown straight away.
// Short and long: a button shows or hides the model answer and explanation.
export default function AnswerCard({ question, number, isPdf }) {
  const [revealed, setRevealed] = useState(false) // written questions only

  const isMcq = question.type === 'mcq'
  const options = question.options || []
  const source = question.source
  const label = source ? pageLabel(source, isPdf) : ''
  const showDetails = isMcq ? true : revealed

  return (
    <article className="question review">
      <div className="question-head">
        <span className="question-number">Question {number}</span>
        <span className="result-tag neutral">{TYPE_LABELS[question.type] || 'Question'}</span>
      </div>

      <h3 className="question-text">{question.question}</h3>

      {isMcq && (
        <div className="options">
          {options.map((option, i) => {
            const isCorrect = i === question.correct_index
            return (
              <div key={i} className={`option-review ${isCorrect ? 'correct' : ''}`}>
                <span className="option-letter">{LETTERS[i]}</span>
                <span>{option}</span>
                {isCorrect && <span className="option-note">Correct answer</span>}
              </div>
            )
          })}
        </div>
      )}

      {!isMcq && (
        <button type="button" className="btn-primary" onClick={() => setRevealed(!revealed)}>
          {revealed ? 'Hide answer' : 'Show answer'}
        </button>
      )}

      {showDetails && !isMcq && (
        <div className="written">
          <p className="label">Model answer</p>
          {question.model_answer ? (
            <p className="model-answer" style={{ whiteSpace: 'pre-wrap' }}>{question.model_answer}</p>
          ) : (
            <p className="model-answer">No model answer was returned for this question.</p>
          )}
        </div>
      )}

      {showDetails && question.explanation && (
        <div className="explanation">
          <p className="label">Explanation</p>
          <p>{question.explanation}</p>
        </div>
      )}

      {showDetails && source && (source.chapter || label) && (
        <p className="review-source">
          Source: {source.chapter || 'Chapter not detected'}
          {label ? `, ${label}` : ''}
        </p>
      )}
    </article>
  )
}
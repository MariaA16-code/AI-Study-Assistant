import { pageLabel } from '../utils/sources.js'

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

// the small badge at the top right of each reviewed question
function resultTag(isMcq, unanswered, isCorrect) {
  if (!isMcq) return <span className="result-tag neutral">Not auto-marked</span>
  if (unanswered) return <span className="result-tag neutral">Not answered</span>
  if (isCorrect) return <span className="result-tag correct">Correct</span>
  return <span className="result-tag wrong">Incorrect</span>
}

// One question on the results page, with the right answer, the explanation and the source.
export default function ReviewCard({ question, number, writtenAnswer, isPdf }) {
  const isMcq = question.type === 'mcq'
  const options = question.options || []
  const selected = question.selected_index
  const unanswered = isMcq && (selected === null || selected === undefined)
  const source = question.source
  const label = source ? pageLabel(source, isPdf) : ''
  const cardState = isMcq && !unanswered ? (question.is_correct ? 'is-correct' : 'is-wrong') : ''

  return (
    <article className={`question review ${cardState}`}>
      <div className="question-head">
        <span className="question-number">Question {number}</span>
        {resultTag(isMcq, unanswered, question.is_correct)}
      </div>

      <h3 className="question-text">{question.question}</h3>

      {isMcq ? (
        <div className="options">
          {options.map((option, i) => {
            const isCorrect = i === question.correct_index
            const isWrongPick = i === selected && !isCorrect
            let note = ''
            if (isCorrect) note = 'Correct answer'
            else if (isWrongPick) note = 'Your answer'

            return (
              <div key={i} className={`option-review ${isCorrect ? 'correct' : ''} ${isWrongPick ? 'wrong' : ''}`}>
                <span className="option-letter">{LETTERS[i]}</span>
                <span>{option}</span>
                {note && <span className="option-note">{note}</span>}
              </div>
            )
          })}
        </div>
      ) : (
        <div className="written">
          <div>
            <p className="label">Your answer</p>
            <p className="your-answer">
              {writtenAnswer && writtenAnswer.trim() ? writtenAnswer : 'You did not write an answer.'}
            </p>
          </div>
          {question.model_answer && (
            <div>
              <p className="label">Model answer</p>
              <p className="model-answer">{question.model_answer}</p>
            </div>
          )}
        </div>
      )}

      {question.explanation && (
        <div className="explanation">
          <p className="label">Explanation</p>
          <p>{question.explanation}</p>
        </div>
      )}

      {source && (source.chapter || label) && (
        <p className="review-source">
          Source: {source.chapter || 'Chapter not detected'}
          {label ? `, ${label}` : ''}
        </p>
      )}
    </article>
  )
}
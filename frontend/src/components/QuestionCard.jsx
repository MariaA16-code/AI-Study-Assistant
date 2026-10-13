const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

// One question on the quiz page. MCQs show option buttons; written questions show a text box.
export default function QuestionCard({ question, number, selected, text, onSelect, onText }) {
  return (
    <article className="question">
      <div className="question-head">
        <span className="question-number">Question {number}</span>
        {question.difficulty && (
          <span className={`level level-${question.difficulty}`}>{question.difficulty}</span>
        )}
      </div>

      <h3 className="question-text">{question.question}</h3>

      {question.type === 'mcq' ? (
        <div className="options" role="radiogroup">
          {question.options.map((option, i) => (
            <button
              key={i}
              type="button"
              role="radio"
              aria-checked={selected === i}
              className={`option ${selected === i ? 'selected' : ''}`}
              onClick={() => onSelect(question.index, i)}
            >
              <span className="option-letter">{LETTERS[i]}</span>
              <span>{option}</span>
            </button>
          ))}
        </div>
      ) : (
        <textarea
          className="answer-box"
          rows={question.type === 'long' ? 8 : 4}
          placeholder="Write your answer here..."
          value={text}
          onChange={(e) => onText(question.index, e.target.value)}
        />
      )}
    </article>
  )
}
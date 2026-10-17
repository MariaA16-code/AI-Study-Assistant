import { pageLabel } from '../utils/sources.js'
import AnswerText from './AnswerText.jsx'
import './StudyGuide.css'

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']
const EMPTY_TEXT = 'Not enough information in the document for this section.'

// one numbered section of the guide; an empty section says so instead of showing nothing
function Section({ number, title, empty, children }) {
  return (
    <section className="guide-section">
      <h3 className="guide-title">
        <span className="guide-number">{number}</span>
        {title}
      </h3>
      {empty ? <p className="hint">{EMPTY_TEXT}</p> : children}
    </section>
  )
}

function SourceLine({ source, isPdf }) {
  if (!source || (!source.chapter && source.page == null)) return null
  const label = pageLabel(source, isPdf)
  return (
    <p className="guide-source">
      Source: {source.chapter || 'Chapter not detected'}
      {label ? `, ${label}` : ''}
    </p>
  )
}

// Shows a revision guide: summary, concepts, definitions, practice questions with answers, topics.
export default function StudyGuide({ guide, isPdf }) {
  const concepts = guide.key_concepts || []
  const definitions = guide.definitions || []
  const shortQuestions = guide.short_questions || []
  const longQuestions = guide.long_questions || []
  const mcqs = guide.mcqs || []
  const topics = guide.revision_topics || []
  const warnings = guide.warnings || []

  return (
    <div className="guide">
      {warnings.length > 0 && (
        <div className="banner">
          {warnings.map((w, i) => (
            <p key={i}>{w}</p>
          ))}
        </div>
      )}

      <Section number={1} title="Summary" empty={!guide.summary}>
        <AnswerText text={guide.summary} />
      </Section>

      <Section number={2} title="Important topics and key concepts" empty={concepts.length === 0}>
        <ul className="chips">
          {concepts.map((c, i) => (
            <li key={i} className="chip">{c}</li>
          ))}
        </ul>
      </Section>

      <Section number={3} title="Important definitions and facts" empty={definitions.length === 0}>
        <ul className="guide-list">
          {definitions.map((d, i) => (
            <li key={i} className="guide-item">
              <p className="guide-term">{d.term}</p>
              <p className="guide-text">{d.definition}</p>
              <SourceLine source={d.source} isPdf={isPdf} />
            </li>
          ))}
        </ul>
      </Section>

      <Section number={4} title="Possible short questions with answers" empty={shortQuestions.length === 0}>
        <ul className="guide-list">
          {shortQuestions.map((q, i) => (
            <li key={i} className="guide-item">
              <p className="guide-term">{q.question}</p>
              <p className="guide-answer">{q.answer}</p>
              <SourceLine source={q.source} isPdf={isPdf} />
            </li>
          ))}
        </ul>
      </Section>

      <Section number={5} title="Possible long questions with answer outlines" empty={longQuestions.length === 0}>
        <ul className="guide-list">
          {longQuestions.map((q, i) => (
            <li key={i} className="guide-item">
              <p className="guide-term">{q.question}</p>
              <ol className="guide-outline">
                {(q.answer_outline || []).map((point, j) => (
                  <li key={j}>{point}</li>
                ))}
              </ol>
              <SourceLine source={q.source} isPdf={isPdf} />
            </li>
          ))}
        </ul>
      </Section>

      <Section number={6} title="Possible MCQs with correct answers" empty={mcqs.length === 0}>
        <ul className="guide-list">
          {mcqs.map((q, i) => (
            <li key={i} className="guide-item">
              <p className="guide-term">{q.question}</p>
              <div className="options">
                {(q.options || []).map((option, j) => {
                  const isCorrect = j === q.correct_index
                  return (
                    <div key={j} className={`option-review ${isCorrect ? 'correct' : ''}`}>
                      <span className="option-letter">{LETTERS[j]}</span>
                      <span>{option}</span>
                      {isCorrect && <span className="option-note">Correct answer</span>}
                    </div>
                  )
                })}
              </div>
              {q.explanation && (
                <div className="explanation">
                  <p className="label">Explanation</p>
                  <p>{q.explanation}</p>
                </div>
              )}
              <SourceLine source={q.source} isPdf={isPdf} />
            </li>
          ))}
        </ul>
      </Section>

      <Section number={7} title="Important topics to revise for the exam" empty={topics.length === 0}>
        <ul className="chips">
          {topics.map((t, i) => (
            <li key={i} className="chip">{t}</li>
          ))}
        </ul>
      </Section>
    </div>
  )
}
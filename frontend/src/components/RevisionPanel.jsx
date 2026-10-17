import { useState } from 'react'
import { getStudyGuide } from '../api.js'
import { getGuide, saveGuide } from '../utils/guideStore.js'
import Spinner from './Spinner.jsx'
import StudyGuide from './StudyGuide.jsx'
import './StudyGuide.css'

// The first thing a student sees for a document: revise, then start the quiz.
export default function RevisionPanel({ doc, onStartQuiz }) {
  const isPdf = doc.title.toLowerCase().endsWith('.pdf')
  const [guide, setGuide] = useState(() => getGuide(doc.id))
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function createGuide() {
    if (loading) return // stops double clicks
    setError('')
    setLoading(true)
    try {
      const result = await getStudyGuide(doc.id)
      saveGuide(doc.id, result)
      setGuide(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="generating">
        <Spinner size={26} />
        <div>
          <strong>Creating your revision guide...</strong>
          <p>This can take from 10 seconds to a minute or more. Please keep this page open.</p>
        </div>
      </div>
    )
  }

  if (!guide) {
    return (
      <div>
        <div className="revision-intro">
          <h3>Revise first, then test yourself</h3>
          <p>
            The revision guide gives you a summary, key concepts, definitions, practice questions with answers,
            and the topics to revise. Everything comes from this document.
          </p>
          <div className="revision-actions">
            <button className="btn-primary" type="button" onClick={createGuide}>Create revision guide</button>
            <button className="link-btn" type="button" onClick={onStartQuiz}>Skip to quiz</button>
          </div>
        </div>
        {error && <p className="error">{error}</p>}
      </div>
    )
  }

  return (
    <div>
      <div className="revision-actions">
        <button className="btn-primary" type="button" onClick={onStartQuiz}>Start quiz</button>
        <button className="link-btn" type="button" onClick={createGuide}>Create the guide again</button>
      </div>
      {error && <p className="error">{error}</p>}

      <StudyGuide guide={guide} isPdf={isPdf} />

      <div className="revision-actions">
        <button className="btn-primary" type="button" onClick={onStartQuiz}>Start quiz</button>
      </div>
    </div>
  )
}
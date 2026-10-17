import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getDocuments } from '../api.js'
import ChatPanel from '../components/ChatPanel.jsx'
import GeneratePanel from '../components/GeneratePanel.jsx'
import RevisionPanel from '../components/RevisionPanel.jsx'

const TABS = [
  { id: 'revision', label: 'Revision' },
  { id: 'chat', label: 'Chat' },
  { id: 'quiz', label: 'Quiz' },
]

export default function Workspace() {
  const { documentId } = useParams()
  const id = Number(documentId)
  const [doc, setDoc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('revision') // students start with the revision guide

  useEffect(() => {
    getDocuments()
      .then((docs) => setDoc(docs.find((d) => d.id === id) || null))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  const back = (
    <Link className="back-link" to="/documents">← Back to documents</Link>
  )

  if (loading) return <p>Loading workspace...</p>

  if (error) {
    return (
      <section>
        {back}
        <p className="error">{error}</p>
      </section>
    )
  }

  if (!doc) {
    return (
      <section>
        {back}
        <p className="empty">Document not found.</p>
      </section>
    )
  }

  if (doc.status !== 'ready') {
    return (
      <section>
        {back}
        <p className="empty">This document is not ready yet. Please wait until its status is "ready".</p>
      </section>
    )
  }

  return (
    <section>
      {back}
      <div className="workspace-head">
        <h2>{doc.title}</h2>
        <span className="badge badge-ready">ready</span>
      </div>

      <div className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`tab ${tab === t.id ? 'active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* all tabs stay mounted, so the guide, the chat and the form choices are kept when you switch tabs */}
      <div hidden={tab !== 'revision'}>
        <RevisionPanel doc={doc} onStartQuiz={() => setTab('quiz')} />
      </div>
      <div hidden={tab !== 'chat'}>
        <ChatPanel doc={doc} />
      </div>
      <div hidden={tab !== 'quiz'}>
        <GeneratePanel doc={doc} />
      </div>
    </section>
  )
}
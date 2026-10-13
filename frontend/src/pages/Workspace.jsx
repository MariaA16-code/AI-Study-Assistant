import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getDocuments } from '../api.js'
import ChatPanel from '../components/ChatPanel.jsx'
import GeneratePanel from '../components/GeneratePanel.jsx'

export default function Workspace() {
  const { documentId } = useParams()
  const id = Number(documentId)
  const [doc, setDoc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('chat') // 'chat' or 'generate'

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
        <button type="button" className={`tab ${tab === 'chat' ? 'active' : ''}`} onClick={() => setTab('chat')}>
          Chat
        </button>
        <button type="button" className={`tab ${tab === 'generate' ? 'active' : ''}`} onClick={() => setTab('generate')}>
          Generate
        </button>
      </div>

      {/* both tabs stay mounted, so the chat history and the form choices are kept when you switch tabs */}
      <div hidden={tab !== 'chat'}>
        <ChatPanel doc={doc} />
      </div>
      <div hidden={tab !== 'generate'}>
        <GeneratePanel doc={doc} />
      </div>
    </section>
  )
}
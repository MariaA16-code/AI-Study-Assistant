import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getDocuments } from '../api.js'
import ChatPanel from '../components/ChatPanel.jsx'
import FileSelector from '../components/FileSelector.jsx'
import GeneratePanel from '../components/GeneratePanel.jsx'

const MAX_FILES = 10

const TABS = [
  { id: 'generate', label: 'Generate' },
  { id: 'chat', label: 'Chat' },
]

// "/workspace/23" is one file; "/workspace/23,24,25" is one shared workspace for several files
function parseIds(param) {
  const ids = String(param || '')
    .split(',')
    .map(Number)
    .filter((n) => Number.isInteger(n) && n > 0)
  return [...new Set(ids)].slice(0, MAX_FILES)
}

export default function Workspace() {
  const { documentId } = useParams()
  const navigate = useNavigate()
  const routeIds = parseIds(documentId)

  const [allDocs, setAllDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('generate')

  useEffect(() => {
    getDocuments()
      .then(setAllDocs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

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

  // only ready documents can be used; the list keeps the order of the documents page,
  // and that same order is used in every request
  const readyDocs = allDocs.filter((d) => d.status === 'ready')
  const docs = readyDocs.filter((d) => routeIds.includes(d.id))

  if (docs.length === 0) {
    const only = routeIds.length === 1 ? allDocs.find((d) => d.id === routeIds[0]) : null
    let text = 'Document not found.'
    if (routeIds.length > 1) text = 'None of the selected files are ready or available.'
    else if (only) text = 'This document is not ready yet. Please wait until its status is "ready".'
    return (
      <section>
        {back}
        <p className="empty">{text}</p>
      </section>
    )
  }

  const several = docs.length > 1
  const skipped = routeIds.length - docs.length
  const selectionKey = docs.map((d) => d.id).join('-')

  function changeSelection(ids) {
    const ordered = readyDocs.filter((d) => ids.includes(d.id)).map((d) => d.id)
    if (ordered.length > 0) navigate(`/workspace/${ordered.join(',')}`, { replace: true })
  }

  return (
    <section>
      {back}
      <div className="workspace-head">
        <h2>{several ? 'Shared workspace' : docs[0].title}</h2>
        <span className="badge badge-ready">{several ? `${docs.length} files` : 'ready'}</span>
      </div>
      {several && <p className="hint">{docs.map((d) => d.title).join(', ')}</p>}
      {skipped > 0 && (
        <p className="warning">
          {skipped} selected {skipped === 1 ? 'file was' : 'files were'} left out because {skipped === 1 ? 'it is' : 'they are'} not ready or not found.
        </p>
      )}

      <FileSelector
        docs={readyDocs}
        selectedIds={docs.map((d) => d.id)}
        maxFiles={MAX_FILES}
        onChange={changeSelection}
      />

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

      {/* both tabs stay mounted, so the chat and the form choices are kept when you switch tabs;
          a new file selection starts fresh panels (and its own chat) */}
      <div hidden={tab !== 'generate'}>
        <GeneratePanel key={`generate-${selectionKey}`} docs={docs} />
      </div>
      <div hidden={tab !== 'chat'}>
        <ChatPanel key={`chat-${selectionKey}`} docs={docs} />
      </div>
    </section>
  )
}
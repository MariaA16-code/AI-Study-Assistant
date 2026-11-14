import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { deleteDocument, getDocuments, uploadDocument } from '../api.js'
import UploadPicker from '../components/UploadPicker.jsx'
import '../components/FileSelector.css'

// same limit as the backend: at most 10 files in one upload or one workspace
const MAX_FILES = 10

// a document is "finished" when it is ready or failed; anything else is still in progress
const isFinished = (status) => status === 'ready' || status === 'failed'

export default function Documents() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')
  const [selectedIds, setSelectedIds] = useState([]) // files ticked for a shared workspace
  const [batchIds, setBatchIds] = useState([]) // files uploaded together in the last upload

  // load the list once when the page opens
  useEffect(() => {
    getDocuments()
      .then(setDocuments)
      .catch((err) => setMessage(err.message))
      .finally(() => setLoading(false))
  }, [])

  // while any document is still processing, refresh the list every 4 seconds
  const hasProcessing = documents.some((d) => !isFinished(d.status))

  useEffect(() => {
    if (!hasProcessing) return undefined
    const timer = setInterval(() => {
      getDocuments()
        .then(setDocuments)
        .catch(() => {}) // ignore a failed refresh; the next one will try again
    }, 4000)
    return () => clearInterval(timer)
  }, [hasProcessing])

  // called by the upload picker; returns true when the upload worked, so the picker can clear its list
  async function handleUpload(files) {
    setMessage('')
    setUploading(true)
    try {
      const result = await uploadDocument(files)
      // the backend answers with a list: one new document (status "processing") per file
      const created = Array.isArray(result) ? result : [result]
      setDocuments((prev) => [...created, ...prev])
      if (created.length > 1) {
        // files uploaded together belong together: remember them as one batch
        setBatchIds(created.map((d) => d.id))
        setSelectedIds(created.map((d) => d.id))
      }
      return true
    } catch (err) {
      setMessage(err.message)
      return false
    } finally {
      setUploading(false)
    }
  }

  async function handleDelete(doc) {
    if (!window.confirm(`Delete "${doc.title}"?`)) return
    setMessage('')
    try {
      await deleteDocument(doc.id)
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id))
      setSelectedIds((prev) => prev.filter((id) => id !== doc.id))
      setBatchIds((prev) => prev.filter((id) => id !== doc.id))
    } catch (err) {
      setMessage(err.message)
    }
  }

  function toggle(id) {
    setSelectedIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id)
      return prev.length < MAX_FILES ? [...prev, id] : prev
    })
  }

  // the workspace address lists the files in the same order as this page shows them
  const pathFor = (ids) =>
    `/workspace/${documents.filter((d) => ids.includes(d.id) && d.status === 'ready').map((d) => d.id).join(',')}`

  const pickedReady = documents.filter((d) => d.status === 'ready' && selectedIds.includes(d.id))
  const batchDocs = documents.filter((d) => batchIds.includes(d.id))
  const batchFinished = batchDocs.length > 1 && batchDocs.every((d) => isFinished(d.status))
  const batchReady = batchDocs.filter((d) => d.status === 'ready')

  return (
    <section>
      <div className="page-header">
        <h2>My Documents</h2>
      </div>

      <UploadPicker maxFiles={MAX_FILES} uploading={uploading} onUpload={handleUpload} />

      {message && (
        <p className="error" style={{ whiteSpace: 'pre-line' }}>
          {message}
        </p>
      )}

      {batchDocs.length > 1 && (
        <div className="batch-card">
          {batchFinished && batchReady.length > 0 ? (
            <>
              <span>
                {batchReady.length} of {batchDocs.length} files uploaded together are ready. Open them in one shared
                workspace to chat and generate questions across all of them.
              </span>
              <Link className="link-btn" to={pathFor(batchReady.map((d) => d.id))}>
                Open shared workspace
              </Link>
            </>
          ) : batchFinished ? (
            <span>None of the files uploaded together could be processed.</span>
          ) : (
            <span>
              {batchDocs.length} files uploaded together. The shared workspace opens here when every file is ready (
              {batchDocs.filter((d) => isFinished(d.status)).length} of {batchDocs.length} done).
            </span>
          )}
        </div>
      )}

      {pickedReady.length > 1 && (
        <div className="select-bar">
          <span>{pickedReady.length} files selected</span>
          <Link className="link-btn" to={pathFor(pickedReady.map((d) => d.id))}>
            Open shared workspace
          </Link>
          <button type="button" className="btn-link" onClick={() => setSelectedIds([])}>
            Clear
          </button>
        </div>
      )}

      {loading && <p>Loading documents...</p>}
      {!loading && documents.length === 0 && <p className="empty">No documents yet. Upload one to get started.</p>}

      <ul className="doc-list">
        {documents.map((doc) => (
          <li key={doc.id} className="card">
            <div>
              {doc.status === 'ready' && (
                <input
                  type="checkbox"
                  className="doc-check"
                  checked={selectedIds.includes(doc.id)}
                  disabled={!selectedIds.includes(doc.id) && selectedIds.length >= MAX_FILES}
                  onChange={() => toggle(doc.id)}
                  aria-label={`Select ${doc.title} for a shared workspace`}
                />
              )}
              <strong>{doc.title}</strong>
              <span className={`badge badge-${isFinished(doc.status) ? doc.status : 'processing'}`}>
                {doc.status}
              </span>
              {doc.status === 'failed' && doc.warnings && doc.warnings.length > 0 && (
                <p className="warning">{doc.warnings.join(' ')}</p>
              )}
            </div>
            <div className="card-actions">
              {doc.status === 'ready' && (
                <Link className="link-btn" to={`/workspace/${doc.id}`}>Open workspace</Link>
              )}
              <button className="btn-danger" onClick={() => handleDelete(doc)}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
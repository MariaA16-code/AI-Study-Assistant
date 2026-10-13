import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { deleteDocument, getDocuments, uploadDocument } from '../api.js'

// a document is "finished" when it is ready or failed; anything else is still in progress
const isFinished = (status) => status === 'ready' || status === 'failed'

export default function Documents() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

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

  async function handleUpload(event) {
    const file = event.target.files[0]
    event.target.value = '' // lets the student pick the same file again later
    if (!file) return

    setUploading(true)
    setMessage('')
    try {
      const newDoc = await uploadDocument(file)
      setDocuments((prev) => [newDoc, ...prev])
    } catch (err) {
      setMessage(err.message)
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
    } catch (err) {
      setMessage(err.message)
    }
  }

  return (
    <section>
      <div className="page-header">
        <h2>My Documents</h2>
        <label className={`upload-btn ${uploading ? 'disabled' : ''}`}>
          {uploading ? 'Uploading...' : 'Upload document'}
          <input type="file" accept=".pdf,.docx,.txt" onChange={handleUpload} disabled={uploading} />
        </label>
      </div>
      <p className="hint">PDF, DOCX or TXT, up to 25 MB.</p>

      {message && <p className="error">{message}</p>}
      {loading && <p>Loading documents...</p>}
      {!loading && documents.length === 0 && <p className="empty">No documents yet. Upload one to get started.</p>}

      <ul className="doc-list">
        {documents.map((doc) => (
          <li key={doc.id} className="card">
            <div>
              <strong>{doc.title}</strong>
              <span className={`badge badge-${isFinished(doc.status) ? doc.status : 'processing'}`}>
                {doc.status}
              </span>
              {doc.warnings.map((w, i) => (
                <p key={i} className="warning">{w}</p>
              ))}
            </div>
            <div className="card-actions">
              {doc.status === 'ready' && <Link to={`/workspace/${doc.id}`}>Open workspace</Link>}
              <button className="btn-danger" onClick={() => handleDelete(doc)}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
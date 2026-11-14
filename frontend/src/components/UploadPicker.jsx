import { useRef, useState } from 'react'
import './UploadPicker.css'

const ALLOWED = ['.pdf', '.docx', '.txt']
const MAX_SIZE = 25 * 1024 * 1024 // 25 MB, same as the backend

function extensionOf(name) {
  const dot = name.lastIndexOf('.')
  return dot === -1 ? '' : name.slice(dot).toLowerCase()
}

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// returns a short reason when the backend would reject this file, otherwise an empty string
function problemWith(file) {
  if (!ALLOWED.includes(extensionOf(file.name))) return 'Only PDF, DOCX and TXT files are allowed.'
  if (file.size > MAX_SIZE) return 'This file is larger than 25 MB.'
  return ''
}

// Choose several files, review the list, then upload them together.
// onUpload(files) must return a promise that resolves to true when the upload worked.
export default function UploadPicker({ maxFiles, uploading, onUpload }) {
  const [files, setFiles] = useState([])
  const [note, setNote] = useState('')
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)

  const problems = files.map(problemWith)
  const hasProblem = problems.some(Boolean)

  function addFiles(picked) {
    const incoming = Array.from(picked)
    if (incoming.length === 0) return

    // skip files that are already in the list
    const fresh = incoming.filter((f) => !files.some((c) => c.name === f.name && c.size === f.size))
    const room = Math.max(0, maxFiles - files.length)
    const accepted = fresh.slice(0, room)

    const parts = []
    if (fresh.length < incoming.length) parts.push('Files that were already in the list were skipped.')
    if (fresh.length > accepted.length) {
      parts.push(`You can upload up to ${maxFiles} files at a time, so ${fresh.length - accepted.length} were not added.`)
    }
    setNote(parts.join(' '))
    setFiles([...files, ...accepted])
  }

  function handleInput(event) {
    addFiles(event.target.files)
    event.target.value = '' // lets the student pick the same file again later
  }

  function handleDrop(event) {
    event.preventDefault()
    setDragging(false)
    if (!uploading) addFiles(event.dataTransfer.files)
  }

  function removeFile(index) {
    setFiles(files.filter((_, i) => i !== index))
    setNote('')
  }

  function clearAll() {
    setFiles([])
    setNote('')
  }

  async function handleUpload() {
    if (uploading || files.length === 0 || hasProblem) return
    const ok = await onUpload(files)
    if (ok) clearAll() // on an error the list stays, so the student can fix it
  }

  return (
    <div className="picker">
      <h3 className="picker-title">Select documents</h3>
      <p className="picker-sub">PDF, DOCX or TXT, 25 MB each.</p>

      <label
        className={`dropzone ${dragging ? 'dragging' : ''} ${uploading ? 'disabled' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          if (!uploading) setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <svg className="dropzone-icon" width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <rect x="8" y="8" width="12" height="12" rx="3" />
          <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
        </svg>
        <span className="dropzone-title">Choose files</span>
        <span className="dropzone-hint">Select up to {maxFiles} documents</span>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          multiple
          onChange={handleInput}
          disabled={uploading}
        />
      </label>

      {note && <p className="picker-note">{note}</p>}

      {files.length > 0 && (
        <>
          <span className="picker-count">
            {files.length} {files.length === 1 ? 'file' : 'files'} selected
          </span>

          <ul className="picker-list">
            {files.map((file, i) => (
              <li key={`${file.name}-${file.size}`} className={`picker-item ${problems[i] ? 'bad' : ''}`}>
                <span className="picker-mark" aria-hidden="true">{problems[i] ? '✕' : '✓'}</span>
                <div className="picker-file">
                  <span className="picker-name">{file.name}</span>
                  {problems[i] && <span className="picker-problem">{problems[i]}</span>}
                </div>
                <span className="picker-size">{formatSize(file.size)}</span>
                <button
                  type="button"
                  className="picker-remove"
                  onClick={() => removeFile(i)}
                  disabled={uploading}
                  aria-label={`Remove ${file.name}`}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>

          {hasProblem && <p className="picker-note">Remove the files marked in red to continue.</p>}

          <div className="picker-actions">
            <button
              type="button"
              className="btn-primary picker-upload"
              onClick={handleUpload}
              disabled={uploading || hasProblem}
            >
              {uploading
                ? 'Uploading...'
                : `Upload ${files.length} ${files.length === 1 ? 'document' : 'documents'}`}
            </button>
            <button type="button" className="picker-clear" onClick={clearAll} disabled={uploading}>
              Clear
            </button>
          </div>
        </>
      )}
    </div>
  )
}
import { useState } from 'react'
import './FileSelector.css'

// Choose which ready documents belong to this workspace.
// docs = every ready document, in the order shown on screen. selectedIds = the ticked ones.
export default function FileSelector({ docs, selectedIds, maxFiles, onChange }) {
  const [open, setOpen] = useState(false)
  if (docs.length < 2) return null // nothing to choose from

  const several = selectedIds.length > 1

  function toggle(id) {
    if (selectedIds.includes(id)) {
      if (selectedIds.length === 1) return // always keep at least one file
      onChange(selectedIds.filter((x) => x !== id))
    } else if (selectedIds.length < maxFiles) {
      onChange([...selectedIds, id])
    }
  }

  return (
    <>
      <div className="files-bar">
        <span className="hint" style={{ margin: 0 }}>
          {several ? `${selectedIds.length} files selected` : 'Want to ask or generate across several files?'}
        </span>
        <button type="button" className="files-toggle" onClick={() => setOpen(!open)}>
          {open ? 'Done' : several ? 'Change files' : 'Add more files'}
        </button>
      </div>

      {open && (
        <div className="files-panel">
          <ul className="files-list">
            {docs.map((d) => {
              const ticked = selectedIds.includes(d.id)
              const full = !ticked && selectedIds.length >= maxFiles
              return (
                <li key={d.id}>
                  <label className={`files-item ${full ? 'dim' : ''}`}>
                    <input type="checkbox" checked={ticked} disabled={full} onChange={() => toggle(d.id)} />
                    <span>{d.title}</span>
                  </label>
                </li>
              )
            })}
          </ul>
          <p className="files-note">
            Up to {maxFiles} files. Chat and questions use all ticked files together. The question count is shared
            between the files, and the chapter is not used with several files.
          </p>
        </div>
      )}
    </>
  )
}
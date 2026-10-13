import { mergeSources, pageLabel } from '../utils/sources.js'

export default function SourceList({ sources, isPdf }) {
  const items = mergeSources(sources)
  if (items.length === 0) return null

  return (
    <div className="sources">
      <p className="sources-title">Sources</p>
      <ul>
        {items.map((s, i) => (
          <li key={i} className="source">
            <div className="source-head">
              <span className="source-chapter">{s.chapter || 'Chapter not detected'}</span>
              {pageLabel(s, isPdf) && (
                <span className={`source-page ${isPdf ? '' : 'soft'}`}>{pageLabel(s, isPdf)}</span>
              )}
            </div>
            {s.snippets.map((text, j) => (
              <p key={j} className="snippet">{text}</p>
            ))}
          </li>
        ))}
      </ul>
    </div>
  )
}
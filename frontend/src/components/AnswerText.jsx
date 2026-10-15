import './AnswerText.css'

// a line that starts with "- ", "* ", a bullet dot, or a number like "1." is a list item
const BULLET = /^\s*([-*•]|\d{1,2}[.)])\s+(.*)$/

// Shows answer text with paragraphs and bullet lists (summary answers contain bullet points).
export default function AnswerText({ text }) {
  const blocks = []
  let list = null

  for (const raw of String(text || '').split('\n')) {
    const line = raw.trimEnd()
    const bullet = line.match(BULLET)

    if (bullet) {
      if (!list) {
        list = { type: 'list', items: [] }
        blocks.push(list)
      }
      list.items.push(bullet[2])
    } else if (line.trim() === '') {
      list = null
    } else {
      list = null
      blocks.push({ type: 'p', text: line })
    }
  }

  return (
    <div className="answer-text">
      {blocks.map((block, i) =>
        block.type === 'list' ? (
          <ul key={i}>
            {block.items.map((item, j) => (
              <li key={j}>{item}</li>
            ))}
          </ul>
        ) : (
          <p key={i}>{block.text}</p>
        ),
      )}
    </div>
  )
}
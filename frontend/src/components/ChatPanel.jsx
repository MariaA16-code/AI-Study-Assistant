import { useEffect, useRef, useState } from 'react'
import { askQuestion } from '../api.js'
import { getChat, saveChat } from '../utils/chatStore.js'
import AnswerText from './AnswerText.jsx'
import SourceList from './SourceList.jsx'

const SUGGESTIONS = [
  'What is this document about?',
  'Summarize the main ideas.',
  'What are the key terms I should know?',
]

const NOT_FOUND_TEXT = 'Not found in your material.'
const GENERIC_ERROR = 'Something went wrong. Please try again.'
const ERROR_TEXT = {
  llm_unavailable: 'The AI is busy. Please try again in a minute.',
}

export default function ChatPanel({ doc }) {
  const isPdf = doc.title.toLowerCase().endsWith('.pdf')
  const [messages, setMessages] = useState(() => getChat(doc.id))
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef(null)

  // keep the conversation in memory, so it is still here when you come back from a quiz
  useEffect(() => {
    saveChat(doc.id, messages)
  }, [doc.id, messages])

  // scroll to the newest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  async function send(text) {
    const question = text.trim()
    if (!question || sending) return // stops double clicks while waiting

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text: question }])
    setSending(true)

    try {
      const result = await askQuestion(doc.id, question)
      let reply

      if (result.error) {
        reply = { role: 'assistant', kind: 'error', text: ERROR_TEXT[result.error] || GENERIC_ERROR }
      } else if (!result.found) {
        reply = { role: 'assistant', kind: 'notfound', text: NOT_FOUND_TEXT }
      } else {
        reply = {
          role: 'assistant',
          kind: 'answer',
          text: result.answer,
          mode: result.mode,
          sources: result.sources || [],
        }
      }

      setMessages((prev) => [...prev, reply])
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', kind: 'error', text: err.message }])
    } finally {
      setSending(false)
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    send(input)
  }

  return (
    <div className="chat">
      <div className="chat-log">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p className="chat-empty-title">Ask anything about this document</p>
            <p className="hint">Answers come with the chapter and page where they were found.</p>
            <div className="suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} type="button" className="suggestion" onClick={() => send(s)} disabled={sending}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`bubble-row role-${m.role}`}>
            <div className={`bubble role-${m.role} ${m.kind || ''}`}>
              {m.role === 'user' && <p>{m.text}</p>}

              {m.kind === 'answer' && (
                <>
                  {m.mode === 'summary' && <span className="mode-tag">Summary</span>}
                  <AnswerText text={m.text} />
                </>
              )}

              {m.kind === 'notfound' && (
                <>
                  <p>{m.text}</p>
                  <p className="bubble-hint">Try asking in a more specific way.</p>
                </>
              )}

              {m.kind === 'error' && <p>{m.text}</p>}

              {m.sources && <SourceList sources={m.sources} isPdf={isPdf} />}
            </div>
          </div>
        ))}

        {sending && (
          <div className="bubble-row role-assistant">
            <div className="bubble role-assistant typing">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about this document..."
          maxLength={2000}
          disabled={sending}
        />
        <button className="send-btn" type="submit" disabled={sending || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}
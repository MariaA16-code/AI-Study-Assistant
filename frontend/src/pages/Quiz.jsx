import { useParams } from 'react-router-dom'

export default function Quiz() {
  const { documentId } = useParams()
  return <h2>Quiz for document {documentId}</h2>
}
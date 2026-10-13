import { useParams } from 'react-router-dom'

export default function Workspace() {
  const { documentId } = useParams()
  return <h2>Workspace for document {documentId}</h2>
}
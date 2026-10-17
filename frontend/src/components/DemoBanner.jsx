import './DemoBanner.css'

// Shown on every page while the app uses sample data instead of the real backend.
export default function DemoBanner() {
  return (
    <div className="demo-banner">
      <strong>Demo mode:</strong> answers, chapters, quizzes and revision guides are sample data.
      Uploaded files are not read. To use the real backend, set USE_MOCK to false in src/api.js.
    </div>
  )
}
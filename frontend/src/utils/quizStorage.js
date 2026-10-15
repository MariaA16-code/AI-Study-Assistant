// Keeps the quiz in the browser's sessionStorage, so refreshing the page does not lose it.

const quizKey = (id) => `study_quiz_${id}`
const writtenKey = (id) => `study_written_${id}`

export function saveQuiz(quiz) {
  try {
    sessionStorage.setItem(quizKey(quiz.attempt_id), JSON.stringify(quiz))
  } catch {
    // storage is not available, so the quiz only lives until the page is refreshed
  }
}

export function loadQuiz(attemptId) {
  try {
    const raw = sessionStorage.getItem(quizKey(attemptId))
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

// written answers are not sent to the backend (it does not mark them), so we keep them here
export function saveWritten(attemptId, answers) {
  try {
    sessionStorage.setItem(writtenKey(attemptId), JSON.stringify(answers))
  } catch {
    // ignore
  }
}

export function loadWritten(attemptId) {
  try {
    const raw = sessionStorage.getItem(writtenKey(attemptId))
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

// called on logout, so a second account in the same browser never sees the first one's quizzes
export function clearQuizStorage() {
  try {
    Object.keys(sessionStorage)
      .filter((key) => key.startsWith('study_quiz_') || key.startsWith('study_written_'))
      .forEach((key) => sessionStorage.removeItem(key))
  } catch {
    // ignore
  }
}
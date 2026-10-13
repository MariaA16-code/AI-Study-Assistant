export const mockDocuments = [
  { id: 1, title: 'Operating Systems.pdf', file: '/media/os.pdf', status: 'ready', warnings: [], pages: 320, chunks: 410, created_at: '2026-10-11T10:00:00Z' },
  { id: 2, title: 'Networking Notes.docx', file: '/media/net.docx', status: 'processing', warnings: [], pages: 0, chunks: 0, created_at: '2026-10-12T09:00:00Z' },
  { id: 3, title: 'Lecture 5.txt', file: '/media/l5.txt', status: 'failed', warnings: ['Could not read the file.'], pages: 0, chunks: 0, created_at: '2026-10-12T09:30:00Z' },
]

export const mockChapters = [
  'Chapter 1. Introduction',
  'Chapter 3. Processes',
  'Chapter 4. Threads',
]

// found: true, with a repeated page (this happens with DOCX files)
export const mockAnswer = {
  answer: 'A process is a program in execution, with its own memory space and resources.',
  found: true,
  sources: [
    { chapter: 'Chapter 3. Processes', page: 84, page_end: 84, snippet: 'A process is a program in execution...' },
    { chapter: 'Chapter 3. Processes', page: 84, page_end: 84, snippet: 'Each process has its own address space...' },
    { chapter: null, page: null, page_end: null, snippet: 'Processes are managed by the scheduler...' },
  ],
}

export const mockNotFound = {
  answer: "I couldn't find this in the uploaded material.",
  found: false,
  sources: [],
}

export const mockLlmDown = {
  answer: '',
  found: false,
  sources: [],
  error: 'llm_unavailable',
}

// What POST /api/quiz/start/ returns: no correct answers, and each question has an index
export const mockQuizStart = {
  attempt_id: 501,
  questions: [
    {
      index: 0,
      type: 'mcq',
      question: 'What is a process?',
      options: ['A program on disk', 'A program in execution', 'A kind of file', 'A hardware device'],
      difficulty: 'medium',
      source: { chapter: 'Chapter 3. Processes', page: 84, page_end: 84, snippet: '' },
    },
    {
      index: 1,
      type: 'mcq',
      question: 'Which resource do threads of the same process share?',
      options: ['Program counter', 'Stack', 'Address space', 'CPU registers'],
      difficulty: 'medium',
      source: { chapter: 'Chapter 4. Threads', page: 120, page_end: 120, snippet: '' },
    },
    {
      index: 2,
      type: 'short',
      question: 'Define a thread.',
      difficulty: 'medium',
      source: { chapter: 'Chapter 4. Threads', page: 118, page_end: 118, snippet: '' },
    },
  ],
  requested: 4,
  warnings: ['Only 3 of 4 questions passed validation.'],
}

// Used only by the mock review. The real backend sends these after the quiz is submitted.
export const mockQuizAnswerKey = {
  0: { correct_index: 1, explanation: 'A process is a program that is currently being executed.' },
  1: { correct_index: 2, explanation: 'Threads of one process share its address space (code, data and heap).' },
  2: { model_answer: 'A thread is the smallest unit of execution inside a process.' },
}
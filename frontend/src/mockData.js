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

// an overview answer: the text already has a summary plus bullet points
export const mockSummary = {
  answer:
    'This document is an introduction to operating systems.\n\n- Processes are programs in execution.\n- Threads are units of execution inside a process.\n- The scheduler decides which process runs next.\n- Memory is divided between processes and kept separate.',
  found: true,
  mode: 'summary',
  sources: [
    { chapter: 'Chapter 1. Introduction', page: 1, page_end: 12, snippet: '' },
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
}// Demo data for the revision guide. The shape below is a PROPOSAL.
// Zainab and Maria still have to confirm the real shape before we rely on it.
export const mockStudyGuide = {
  summary:
    'This document is an introduction to operating systems.\n\n- A process is a program in execution.\n- Threads are units of execution inside a process.\n- The scheduler decides which process runs next.',
  key_concepts: ['Processes', 'Threads', 'Scheduling', 'Memory management'],
  definitions: [
    {
      term: 'Process',
      definition: 'A program that is currently being executed.',
      source: { chapter: 'Chapter 3. Processes', page: 84, page_end: 84 },
    },
    {
      term: 'Thread',
      definition: 'The smallest unit of execution inside a process.',
      source: { chapter: 'Chapter 4. Threads', page: 118, page_end: 118 },
    },
  ],
  short_questions: [
    {
      question: 'What is a process?',
      answer: 'A program in execution, with its own memory space and resources.',
      source: { chapter: 'Chapter 3. Processes', page: 84, page_end: 84 },
    },
    {
      question: 'Name one resource that threads of the same process share.',
      answer: 'The address space (code, data and heap).',
      source: { chapter: 'Chapter 4. Threads', page: 120, page_end: 120 },
    },
  ],
  long_questions: [
    {
      question: 'Explain the difference between a process and a thread.',
      answer_outline: [
        'Define a process and a thread.',
        'A process has its own address space; the threads of one process share it.',
        'Threads are cheaper to create and to switch between.',
        'Give one example of when to use each.',
      ],
      source: { chapter: 'Chapter 4. Threads', page: 118, page_end: 121 },
    },
  ],
  mcqs: [
    {
      question: 'What is a process?',
      options: ['A program on disk', 'A program in execution', 'A kind of file', 'A hardware device'],
      correct_index: 1,
      explanation: 'A process is a program that is currently being executed.',
      source: { chapter: 'Chapter 3. Processes', page: 84, page_end: 84 },
    },
  ],
  revision_topics: ['Process states and transitions', 'Scheduling algorithms', 'Threads versus processes'],
  warnings: [],
}
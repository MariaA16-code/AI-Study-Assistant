# AI Study Assistant

A web app where a student uploads a study document (PDF, DOCX or TXT), asks questions about it, and generates practice questions from it. Every answer and question comes with its source (chapter and page) taken from the uploaded document only.

## Features

- Sign up and log in; each student sees only their own documents and quiz attempts.
- Upload PDF, DOCX or TXT files (max 25 MB). Documents are processed in the background.
- **Chat**: ask questions about a document and get answers with sources.
- **Generate questions**: multiple choice, short, long or mixed, by chapter and difficulty (1–20 questions).
- **Quiz mode**: take the questions, submit, and review correct answers, explanations and sources. Only multiple-choice questions are scored automatically.
- Summaries of a whole document or a chapter.

## How it fits together

```
Browser (React + Vite, port 5173)
        |  /api requests (proxied by Vite)
        v
Django REST backend (port 8000)  --->  ai_service (Python package)
        |                                 - extracts text, splits into chunks
   SQLite database                        - embeddings (fastembed) + ChromaDB
                                          - Gemini, with Groq as fallback
```

| Folder | What it is |
|---|---|
| `frontend/` | React 19 + Vite user interface |
| `backend/` | Django 5 + Django REST Framework API (auth, documents, chat, quizzes) |
| `ai_service/` | AI logic: text extraction, retrieval, answering, question generation, validation |
| `requirements.txt` | Installs the backend and AI service packages together |
| `.env.example` | Template for your own settings and API keys |

## Requirements

- **Git**
- **Python 3.10, 3.11 or 3.12** (check with `python --version`)
- **Node.js 20.19 or newer** (check with `node --version`)
- **A Gemini API key** and/or **a Groq API key** (both have free tiers)
- Internet access: the first document upload downloads a small embedding model (about 130 MB), and the AI providers are online services

## Setup

### 1. Get the code

```bash
git clone https://github.com/MariaA16-code/AI-Study-Assistant.git
cd AI-Study-Assistant
```

### 2. Create your `.env` file

Copy the template to the **project root** and fill it in (see the comments inside the file):

```bash
# Windows (PowerShell)
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

At minimum set `SECRET_KEY`, `DEBUG=True` and at least one of `GEMINI_API_KEY` / `GROQ_API_KEY`. To make a secret key (run this after step 3):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Backend and AI service

From the project root:

```bash
# create and activate a virtual environment
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# if PowerShell blocks it, run once: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# macOS / Linux
source venv/bin/activate

# install everything (backend + ai_service)
pip install -r requirements.txt
```

Create the database and start the server:

```bash
cd backend
python manage.py migrate
python manage.py runserver --noreload
```

Keep this terminal open. The API is now at http://127.0.0.1:8000 and the interactive API docs are at http://127.0.0.1:8000/api/docs/.

> Always start the server with `--noreload` and as a single process. Documents are processed in a background thread, and the auto-reloader would run two processes.

### 4. Frontend

Open a **second terminal**:

```bash
cd frontend
npm install
```

**Important:** open `frontend/src/api.js` and make sure this line says `false`:

```js
const USE_MOCK = false
```

With `true` the app shows fake demo data and never talks to the backend (uploads, chat and quizzes will not be real).

Then start the interface:

```bash
npm run dev
```

Open http://localhost:5173 in your browser.

### 5. Use it

1. Click to register a new account (password at least 8 characters), then log in.
2. Upload a PDF, DOCX or TXT file and wait until its status changes from "processing" to "ready". The first upload is slower because the embedding model downloads.
3. Open the document. Use **Chat** to ask questions, or **Generate** to create questions and take a quiz.

## Running the tests

From the project root with the virtual environment active:

```bash
python -m pytest ai_service/tests -q
```

End-to-end check of the AI service with a real file and your API keys:

```bash
python -m ai_service.smoke_test "path/to/file.pdf" "a question the file answers"
```

## Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| Backend stops with `UndefinedValueError: SECRET_KEY` | There is no `.env` in the project root, or it has no `SECRET_KEY`. |
| Every request returns `400 Bad Request` | Set `DEBUG=True` in `.env` and restart the backend. |
| The app shows the same "Operating Systems" quiz for every document | `USE_MOCK` in `frontend/src/api.js` is still `true`. Set it to `false` and restart `npm run dev`. |
| "The AI is busy. Please try again in a minute." | The Gemini/Groq key is missing or wrong, or the free quota is used up. Check `.env` and restart the backend after any change. |
| Network errors in the browser | The backend is not running on port 8000, or the frontend was not started with `npm run dev` (the dev server forwards `/api` to the backend). |
| Document stays on "processing" or becomes "failed" | The first upload downloads the embedding model, so wait and check your internet. Look at the backend terminal for the error. Documents are processed one at a time. |
| Fewer questions than requested | Generated questions are checked for quality and some are rejected. The app shows a warning. Try again, or raise `GEN_RETRIES` / `GEN_EXTRA_ROUNDS` in `.env`. |
| `npm install` complains about peer dependencies | The project already includes `frontend/.npmrc` for this. Make sure you ran the command inside `frontend/`. |
| Want to start from scratch | Stop the backend and delete `backend/db.sqlite3`, `backend/media/` and `chroma_db/`, then run `python manage.py migrate` again. |

## Notes

- The database (`db.sqlite3`), uploaded files (`media/`) and document vectors (`chroma_db/`) are created locally and are not part of the repository.
- Never commit your `.env` file or API keys.
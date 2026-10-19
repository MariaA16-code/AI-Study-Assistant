# AI Study Assistant

A web app where a student uploads a study document (PDF, DOCX or TXT), asks questions about it, and generates practice questions from it. Every answer and question comes with its source (chapter and page) taken from the uploaded document only.

## Features

- Sign up and log in; each student sees only their own documents and quiz attempts.
- Upload PDF, DOCX or TXT files (max 25 MB). Documents are processed in the background.
- **Chat**: ask questions about a document and get answers with sources.
- **Diagrams, charts and pictures**: Gemini vision describes them during upload (for example `A -> B` for flowchart arrows), so chat can answer questions about them. Scanned PDF pages are read with OCR.
- **Generate questions**: multiple choice, short, long or mixed, by chapter and difficulty (1-20 questions).
- **Quiz mode**: take the questions, submit, and review correct answers, explanations and sources. Only multiple-choice questions are scored automatically; for short and long questions you compare your answer with the model answer.
- Summaries of a whole document or a chapter.

## How it fits together

```
Browser (React + Vite, port 5173)
        |  /api requests (proxied by Vite)
        v
Django REST backend (port 8000)  --->  ai_service (Python package)
        |                                 - extracts text, tables and pictures, splits into chunks
   SQLite database                        - embeddings (fastembed) + ChromaDB
                                          - Gemini (with Groq as fallback for text)
                                          - Gemini vision for pictures, OCR as fallback
```

| Folder | What it is |
|---|---|
| `frontend/` | React 19 + Vite user interface |
| `backend/` | Django 5 + Django REST Framework API (auth, documents, chat, quizzes) |
| `ai_service/` | AI logic: text extraction, vision, retrieval, answering, question generation, validation |
| `requirements.txt` | Installs the backend and AI service packages together |
| `.env.example` | Template for your own settings and API keys |

## Requirements

- **Python 3.10, 3.11 or 3.12** (check with `python --version`)
- **Node.js 20.19 or newer** (check with `node --version`)
- **A Gemini API key** (free tier is enough for a demo). A Groq key can be added as a fallback for chat and quizzes. **Reading pictures and diagrams needs the Gemini key**; with only a Groq key the app still works, but diagram questions will not be answered.
- Internet access: the first document upload downloads a small embedding model (about 130 MB), and the AI providers are online services
- Git, only if you get the code with `git clone` instead of a zip file

## Quick start (Windows PowerShell)

Open two terminals in the project folder. Details for each step are below.

```powershell
# Terminal 1: backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env        # then edit .env: SECRET_KEY, DEBUG=True, GEMINI_API_KEY
cd backend
python manage.py migrate
python manage.py runserver --noreload

# Terminal 2: frontend
cd frontend
npm install
npm run dev                   # open http://localhost:5173
```

## Setup

### 1. Get the code

Unzip the project folder, or clone it:

```bash
git clone https://github.com/MariaA16-code/AI-Study-Assistant.git
cd AI-Study-Assistant
```

### 2. Backend packages

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

### 3. Create your `.env` file

Copy the template to the **project root** (the same folder as this README):

```bash
# Windows (PowerShell)
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and set:

- `SECRET_KEY`: make one with this command (it needs step 2 to be done first), and paste the result after `SECRET_KEY=`:
```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
- `DEBUG=True` (the backend rejects every request when it is not True)
- `GEMINI_API_KEY=` your own key (and/or `GROQ_API_KEY=`)

Rules for `.env`: no spaces around `=`, no quotes needed, and **never put a comment on the same line as a value**.

**Vision models (optional).** By default pictures are described with the same model as chat (`GEMINI_MODEL`). Some Gemini models are busy at times or closed to new accounts, so you can set `VISION_MODEL` and `VISION_FALLBACK_MODEL` to two different models that **your own key can use**. If a model name returns "404 NOT_FOUND" in the backend terminal, your key cannot use it; choose another one from Google AI Studio.

### 4. Create the database and start the backend

```bash
cd backend
python manage.py migrate
python manage.py runserver --noreload
```

Keep this terminal open. The API is now at http://127.0.0.1:8000 and the interactive API docs are at http://127.0.0.1:8000/api/docs/.

> Always start the server with `--noreload` and as a single process. Documents are processed in a background thread, and the auto-reloader would run two processes. Restart the backend after you change `.env`.

### 5. Frontend

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

### 6. Use it

1. Click to register a new account (password at least 8 characters), then log in. The database is created empty, so there are no existing accounts.
2. Upload a PDF, DOCX or TXT file and wait until its status changes from "processing" to "ready". The first upload is slower because the embedding model downloads. Files with diagrams take longer, because each figure page or picture is sent to Gemini.
3. Open the document. Use **Chat** to ask questions, or **Generate** to create questions and take a quiz.

## Reading pictures, diagrams and tables

- **PDF**: pages that contain diagrams, charts or large pictures (and pages with drawn tables) are sent to Gemini as page images, up to 20 pages per file. Pages without a text layer (scans) are read with OCR.
- **DOCX**: each picture is described by Gemini, up to 10 per file. Tables made of text are read directly, row by row.
- The descriptions are added to the page text as lines starting with `[Figure]`, so answers can cite the page. Descriptions can contain mistakes, especially arrow directions.
- If Gemini is busy, out of quota, or `VISION_ENABLED=False`, the document still uploads and OCR reads the pictures when it can. **A document that was uploaded while vision failed stays without its diagram text. Delete it and upload it again when Gemini works.**
- **Privacy:** pictures and figure pages are sent to Google. Set `VISION_ENABLED=False` in `.env` to keep everything on your computer.
- Limits and speed settings (`VISION_MAX_PAGES`, `VISION_MAX_IMAGES`, `OCR_DPI`, `OCR_MAX_PAGES`) are in `.env.example`.

## Running the tests

From the project root with the virtual environment active:

```bash
python -m pytest ai_service/tests -q
```

The tests never call Gemini. A few PDF tests are skipped unless `reportlab` is installed (`pip install reportlab`).

End-to-end check of the AI service with a real file and your API keys:

```bash
python -m ai_service.smoke_test "path/to/file.pdf" "a question the file answers"
```

## Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| Backend stops with `UndefinedValueError: SECRET_KEY` | There is no `.env` in the project root, or it has no `SECRET_KEY`. |
| `Invalid truth value` or `invalid literal for int()` at startup | A line in `.env` has a comment after the value. Move the comment to its own line. |
| Every request returns `400 Bad Request` | Set `DEBUG=True` in `.env` and restart the backend. |
| The app shows the same "Operating Systems" quiz for every document | `USE_MOCK` in `frontend/src/api.js` is still `true`. Set it to `false` and restart `npm run dev`. |
| "The AI is busy. Please try again in a minute." | The Gemini/Groq key is missing or wrong, or the free quota is used up. Check `.env` and restart the backend after any change. |
| Questions about a diagram say "not found" | The document was uploaded while vision was off or failing. Look in the backend terminal for `Vision failed`, fix the cause (see the next rows), then delete the document and upload it again. |
| `Vision failed ... 503 UNAVAILABLE` | Google's model is busy. Wait a few minutes, or set `VISION_FALLBACK_MODEL` to a different model. |
| `Vision failed ... 429 RESOURCE_EXHAUSTED` | The Gemini quota is used up (it is shared with chat). Wait for it to reset, or use another key. |
| `Vision failed ... 404 NOT_FOUND` | Your key cannot use that model. Choose a different `VISION_MODEL` or `VISION_FALLBACK_MODEL`. |
| Uploads take a long time | Each figure page or picture is one Gemini call, and scanned pages use OCR. Lower `VISION_MAX_PAGES`, `VISION_MAX_IMAGES` or `OCR_MAX_PAGES`, set `OCR_DPI=150`, or set `VISION_ENABLED=False`. |
| Network errors in the browser | The backend is not running on port 8000, or the frontend was not started with `npm run dev` (the dev server forwards `/api` to the backend). |
| Document stays on "processing" or becomes "failed" | The first upload downloads the embedding model, so wait and check your internet. Look at the backend terminal for the error. Documents are processed one at a time. |
| Fewer questions than requested | Generated questions are checked for quality and some are rejected. The app shows a warning. Try again, or raise `GEN_RETRIES` / `GEN_EXTRA_ROUNDS` in `.env`. |
| `npm install` complains about peer dependencies | The project already includes `frontend/.npmrc` for this. Make sure you ran the command inside `frontend/`. |
| Want to start from scratch | Stop the backend and delete `backend/db.sqlite3`, `backend/media/` and `chroma_db/`, then run `python manage.py migrate` again. |

## Notes

- The database (`db.sqlite3`), uploaded files (`media/`) and document vectors (`chroma_db/`) are created locally and are not part of the project files.
- Never commit or send your `.env` file or API keys.
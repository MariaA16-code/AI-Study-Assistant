# Backend (Django REST API)

Django backend for the AI Study Assistant. Students sign up, upload a file,
chat with it, and take quizzes. The AI part is in ai_service (by Maria).

## Setup
1. Clone the repo and open the backend folder.
2. Create and activate a virtual environment:
   python -m venv venv
   .\venv\Scripts\Activate.ps1
3. Install the packages:
   pip install -r requirements.txt
   pip install -r ../ai_service/requirements.txt
4. Create a .env file in the repo root (never commit it):
   SECRET_KEY=your_secret_key
   DEBUG=True
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_key
   GROQ_API_KEY=your_groq_key
5. Create the database:
   python manage.py migrate
6. Run the server (one process only):
   python manage.py runserver --noreload

API docs (with Try it out): http://127.0.0.1:8000/api/docs/

## Login
Send the token in every request: Authorization: Token <key>
Only register and login are open.

## Endpoints
Auth
- POST /api/auth/register/
- POST /api/auth/login/
- GET  /api/auth/me/

Documents
- POST   /api/documents/            upload (PDF, DOCX, TXT, max 25 MB)
- GET    /api/documents/            list my documents
- GET    /api/documents/{id}/
- DELETE /api/documents/{id}/
- GET    /api/documents/{id}/chapters/

Study
- POST /api/chat/                   ask a question about a document
- POST /api/quiz/generate/          generate questions (not saved)
- POST /api/quiz/start/             start a quiz attempt (saved)
- POST /api/quiz/{attempt_id}/submit/
- GET  /api/quiz/{attempt_id}/review/
- GET  /api/quiz/attempts/          my past attempts

## Notes
- Each student sees only their own documents and attempts.
- Only MCQs are scored automatically.
- Documents are processed one at a time, in the background.
- Quiz generation can return fewer questions than requested.
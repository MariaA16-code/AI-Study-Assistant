"""Reads configuration from the root .env (works with or without Django)."""
from pathlib import Path

from decouple import config

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LLM_PROVIDER = config("LLM_PROVIDER", default="gemini")
GEMINI_API_KEY = config("GEMINI_API_KEY", default="")
GROQ_API_KEY = config("GROQ_API_KEY", default="")
GEMINI_MODEL = config("GEMINI_MODEL", default="gemini-flash-latest")
GROQ_MODEL = config("GROQ_MODEL", default="openai/gpt-oss-120b")
LLM_TIMEOUT = config("LLM_TIMEOUT", default=30, cast=int)  # seconds
CHROMA_DIR = config("CHROMA_DIR", default=str(PROJECT_ROOT / "chroma_db"))
EMBED_MODEL = config("EMBED_MODEL", default="BAAI/bge-small-en-v1.5")
MIN_SCORE = config("MIN_SCORE", default=0.50, cast=float)
TOP_K = config("TOP_K", default=5, cast=int)
GEN_TIMEOUT = config("GEN_TIMEOUT", default=60, cast=int)  # seconds per generation call
MAX_QUESTIONS = config("MAX_QUESTIONS", default=20, cast=int)
LLM_RETRIES = config("LLM_RETRIES", default=1, cast=int)  # extra tries per provider, answers
GEN_RETRIES = config("GEN_RETRIES", default=0, cast=int)  # extra tries per provider, generation
LLM_RETRY_DELAY = config("LLM_RETRY_DELAY", default=1.0, cast=float)  # seconds, grows per try
SUMMARY_PASSAGES = config("SUMMARY_PASSAGES", default=14, cast=int)
GEN_EXTRA_ROUNDS = config("GEN_EXTRA_ROUNDS", default=4, cast=int)  # extra tries to reach the count
GEN_EXTRA_CANDIDATES = config("GEN_EXTRA_CANDIDATES", default=3, cast=int)  # spare questions asked per call
# OCR for scanned PDFs (pages without a text layer)
OCR_ENABLED = config("OCR_ENABLED", default=True, cast=bool)
OCR_MAX_PAGES = config("OCR_MAX_PAGES", default=150, cast=int)  # most scanned pages read per file
OCR_DPI = config("OCR_DPI", default=200, cast=int)  # higher = more accurate but slower
OCR_MAX_IMAGES = config("OCR_MAX_IMAGES", default=60, cast=int)  # most pictures read per DOCX
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
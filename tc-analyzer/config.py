"""
Supports OpenAI, Groq, Google Gemini, and Ollama (local).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Provider
# Options: openai , groq , gemini , ollama
LLM_PROVIDER     = os.getenv("TC_LLM_PROVIDER", "groq")

OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "")

DEFAULT_MODEL    = os.getenv("TC_MODEL", "llama-3.3-70b-versatile")  # Groq default
TEMPERATURE      = float(os.getenv("TC_TEMPERATURE", "0.1"))

# Embeddings 
# huggingface = free, local | openai = paid
EMBED_PROVIDER   = os.getenv("TC_EMBED_PROVIDER", "huggingface")

# RAG 
CHUNK_SIZE       = int(os.getenv("TC_CHUNK_SIZE", "1000"))
CHUNK_OVERLAP    = int(os.getenv("TC_CHUNK_OVERLAP", "200"))
TOP_K            = int(os.getenv("TC_TOP_K", "5"))

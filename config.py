"""
Configuration settings for NeuroSym Crisis.
Supports local offline execution via Ollama or zero-dependency fallback engine.
"""

import os

# Ollama Local Offline AI Configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.environ.get("OLLAMA_LLM_MODEL", "llama3.2")  # e.g., llama3.2, llama3, mistral, gemma2, phi3
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")  # e.g., nomic-embed-text, all-minilm, llama3.2
OLLAMA_TIMEOUT_SECONDS = float(os.environ.get("OLLAMA_TIMEOUT", "0.8"))
OLLAMA_ENABLED = os.environ.get("OLLAMA_ENABLED", "true").lower() in ("true", "1", "yes")

# Disaster Region & Sovereign Authority Defaults
DEFAULT_DISTRICT = "Kanyakumari"
DEFAULT_STATE = "Tamil Nadu"
DEFAULT_SOVEREIGN_AUTHORITY = "District Disaster Management Authority (DDMA)"

# RAG Knowledge Base Paths
KNOWLEDGE_BASE_DIRS = [
    os.path.join(os.path.dirname(__file__), "knowledge_base"),
    os.path.join(os.path.dirname(__file__), "data", "knowledge_base")
]

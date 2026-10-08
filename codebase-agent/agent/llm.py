"""One place that talks to the LLM. Works with ANY OpenAI-compatible server.
Switch providers with env vars only - no code changes:

  Ollama (free, local, default):  nothing to set
  Groq:   LLM_BASE_URL=https://api.groq.com/openai/v1  LLM_API_KEY=...  LLM_MODEL=...
  Gemini: LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/ ...
"""
import os
import time
from openai import OpenAI

BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("LLM_API_KEY", "ollama")      # Ollama ignores the key
MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
RETRIES = 4

_client = None


def chat(messages, tools=None, max_tokens=1500):
    global _client
    if _client is None:
        _client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=300)
    kwargs = dict(model=MODEL, messages=messages, max_tokens=max_tokens, temperature=0.2)
    if tools:
        kwargs["tools"] = tools
    last = None
    for attempt in range(RETRIES):
        try:
            return _client.chat.completions.create(**kwargs)
        except Exception as e:
            last = e
            text = str(e)
            # Small models sometimes emit broken tool-call JSON; asking again usually works.
            if "tool_use_failed" in text or "Failed to parse tool call" in text:
                continue
            if "429" in text or "rate limit" in text.lower():
                time.sleep(5 * (attempt + 1))
                continue
            break
    hint = ("If using Ollama: is it running, and did you run `ollama pull "
            f"{MODEL}`?" if "localhost" in BASE_URL else
            "Try another model (set LLM_MODEL) or wait a minute if you hit a rate limit.")
    raise SystemExit(f"\nLLM call failed ({BASE_URL}, model {MODEL}).\n{hint}\nError: {last}")

from crewai import LLM
import os
from dotenv import load_dotenv

load_dotenv()

# Provider prefix → environment variable name mapping
# CrewAI uses LiteLLM under the hood, which needs provider-specific env vars.
_PROVIDER_ENV_MAP = {
    "openai":     "OPENAI_API_KEY",
    "anthropic":  "ANTHROPIC_API_KEY",
    "google":     "GEMINI_API_KEY",
    "gemini":     "GEMINI_API_KEY",
    "groq":       "GROQ_API_KEY",
    "cohere":     "COHERE_API_KEY",
    "mistral":    "MISTRAL_API_KEY",
    "deepseek":   "DEEPSEEK_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "azure":      "AZURE_API_KEY",
}

def get_llm() -> LLM:
    """
    Returns the configured CrewAI LLM object.

    Configure via .env:
      AI_MODEL   = provider/model-name  (e.g. ollama/qwen2.5:14b, google/gemini-2.0-flash)
      AI_API_KEY = your-api-key-here
    """
    model_name = os.getenv("AI_MODEL", "openai/gpt-4o-mini")
    api_key = os.getenv("AI_API_KEY")

    if model_name.startswith("ollama/"):
        # Local Ollama config — no API key needed
        # We specify the default Ollama local base_url
        return LLM(
            model=model_name,
            base_url="http://localhost:11434"
        )

    # Cloud config
    if not api_key:
        raise ValueError(
            "❌ AI_API_KEY is not set in .env file.\n"
            "Please add: AI_API_KEY=your-api-key-here"
        )

    # Auto-detect provider from model prefix (e.g. "openai/gpt-4o-mini" → "openai")
    provider = model_name.split("/")[0].lower() if "/" in model_name else "openai"
    env_var = _PROVIDER_ENV_MAP.get(provider)

    if env_var:
        os.environ[env_var] = api_key
    else:
        # Fallback: try setting OPENAI_API_KEY for unknown providers
        # (works for OpenAI-compatible APIs)
        os.environ["OPENAI_API_KEY"] = api_key

    return LLM(
        model=model_name,
        api_key=api_key
    )

def get_writer_llm() -> LLM:
    """
    Returns the configured Writer/Director LLM object.
    Falls back to get_llm() if WRITER_MODEL is not set in .env.
    """
    writer_model = os.getenv("WRITER_MODEL")
    if not writer_model:
        return get_llm()

    # Bypasses check if set to local Ollama
    if writer_model.startswith("ollama/"):
        return LLM(
            model=writer_model,
            base_url="http://localhost:11434"
        )

    # Cloud config
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise ValueError(
            "❌ AI_API_KEY is not set in .env. Please add it to use the cloud WRITER_MODEL."
        )

    provider = writer_model.split("/")[0].lower() if "/" in writer_model else "openai"
    env_var = _PROVIDER_ENV_MAP.get(provider)

    if env_var:
        os.environ[env_var] = api_key
    else:
        os.environ["OPENAI_API_KEY"] = api_key

    return LLM(
        model=writer_model,
        api_key=api_key
    )
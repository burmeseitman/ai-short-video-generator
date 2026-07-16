import os
import re
import yaml
import json
from datetime import datetime
from src.config_llm import get_llm

# ─── Config path ──────────────────────────────────────────────────────────────
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PLAN_PATH = os.path.join(_root, "config", "content_plan.yaml")


def _load_plan() -> dict:
    """Load content_plan.yaml and return its parsed contents."""
    with open(_PLAN_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _litellm_model(model: str) -> str:
    """
    Map config model names to their LiteLLM provider prefix equivalents.
    e.g. 'google/gemini-flash-latest' → 'gemini/gemini-flash-latest'
    """
    _prefix_map = {"google": "gemini"}
    parts = model.split("/", 1)
    if len(parts) == 2:
        return f"{_prefix_map.get(parts[0], parts[0])}/{parts[1]}"
    return model


def _clean_topic(raw: str) -> str:
    """
    Extract a clean topic title from a raw LLM response.

    Strategy:
    - Join all non-empty lines into one string (handles multi-line titles)
    - Strip markdown, numbering, asterisks, quotes
    - Filter out lines that look like prompt leakage (contain '):', '->', '**')
    - Trim to a maximum of 90 characters at a word boundary
    """
    cleaned_lines = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # Strip leading numbering like "1." "- " "* "
        line = re.sub(r'^[\d\.\-\*\)]+\s*', '', line).strip()
        # Strip surrounding quotes or asterisks
        line = line.strip('"\'*').strip()
        if line:
            cleaned_lines.append(line)

    if not cleaned_lines:
        raise ValueError(f"Could not extract topic from LLM response: {raw!r}")

    # Join all parts (multi-line title → single line)
    topic = ' '.join(cleaned_lines).strip()

    # Cap at 90 chars at a word boundary
    if len(topic) > 90:
        topic = topic[:90].rsplit(' ', 1)[0].rstrip(' .,;:')

    return topic


def _call_llm(prompt: str, stop: list = None) -> str:
    """
    Send a structured prompt to the configured LLM and return a clean topic title.
    Uses google-genai directly for Gemini models to avoid LiteLLM parsing/truncation errors.
    Falls back to LiteLLM for other models.
    """
    from dotenv import load_dotenv
    load_dotenv(override=True)

    llm_obj = get_llm()
    # Extract string attributes from the CrewAI LLM object
    model = llm_obj.model if hasattr(llm_obj, "model") else str(llm_obj)
    provider = getattr(llm_obj, "provider", None)
    base_url = getattr(llm_obj, "base_url", None)
    api_key = getattr(llm_obj, "api_key", os.getenv("AI_API_KEY"))

    # CrewAI LLM stores model without provider prefix (e.g. model='qwen2.5:14b', provider='ollama')
    # If the provider is ollama, reconstruct the LiteLLM prefix
    if provider == "ollama" and not model.startswith("ollama/"):
        model = f"ollama/{model}"

    # If it is a Gemini/Google model, use the official SDK directly for perfect reliability
    if "google/" in model or "gemini" in model.lower():

        from google import genai

        # Clean model name (e.g. "google/gemini-flash-latest" -> "gemini-flash-latest")
        model_clean = model.replace("google/", "")

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_clean,
            contents=prompt
        )
        content = response.text

    else:
        # Fallback to LiteLLM for other model providers (OpenAI, Anthropic, etc. including Ollama)
        import litellm
        litellm_model = _litellm_model(model)
        kwargs = dict(
            model=litellm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a YouTube Shorts content strategist. Output ONE video topic title only. No explanation, no numbering, no markdown."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=150,
        )
        if stop:
            kwargs["stop"] = stop
        if base_url and provider != "ollama":
            # LiteLLM needs api_base configured for other custom local endpoints
            kwargs["api_base"] = base_url
        if api_key:
            kwargs["api_key"] = api_key


        response = litellm.completion(**kwargs)
        content = response.choices[0].message.content

    if not content:
        raise ValueError("LLM returned empty content.")


    return _clean_topic(content)



def _load_history() -> list:
    history_file = "data/topic_history.json"
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_topic_to_history(topic: str):
    history_file = "data/topic_history.json"
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    history = _load_history()
    # Filter out any existing entries with the same topic (case-insensitive) to prevent duplicates
    history = [h for h in history if h.get("topic", "").strip().lower() != topic.strip().lower()]
    history.append({
        "topic": topic,
        "date": datetime.now().isoformat()
    })
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

def pick_topic_for_today(day_override: str = None) -> dict:
    """
    Look up today's schedule entry and ask the LLM to pick one specific topic.

    Args:
        day_override: Optional weekday name (e.g. 'Monday') for testing.
                      Defaults to today's actual weekday.

    Returns:
        dict with keys: day, category, style, niche, topic
    """
    plan = _load_plan()
    niche    = plan.get("niche", "Tech & Productivity")
    schedule = plan.get("schedule", {})
    day      = day_override or datetime.now().strftime("%A")

    if day not in schedule:
        return {
            "day": day, "category": "General Tech",
            "style": "Trending or Interesting", "niche": niche,
            "topic": f"Latest Trends in {niche}",
        }

    entry    = schedule[day]
    category = entry["category"]
    style    = entry["style"]

    # Retrieve history from last 30 days
    history = _load_history()
    recent_topics = []
    thirty_days_ago = datetime.now().timestamp() - (30 * 24 * 60 * 60)
    
    for h in history:
        try:
            dt = datetime.fromisoformat(h["date"])
            if dt.timestamp() > thirty_days_ago:
                recent_topics.append(h["topic"])
        except Exception:
            pass

    history_instruction = ""
    if recent_topics:
        recent_str = "\\n  - ".join(recent_topics)
        history_instruction = f"\\n- DO NOT output these recent topics or anything closely related:\\n  - {recent_str}"

    prompt = (
        f"Suggest one specific, engaging, and complete YouTube Shorts video topic title in the category: {category}.\\n"
        f"Channel niche: {niche}.\\n"
        f"Requirements:\\n"
        f"- Output ONLY the final title, no other text, intro, or quotes.\\n"
        f"- The title must be in English.\\n"
        f"- Make it specific, detailed, and at least 5 words long.{history_instruction}"
    )

    print(f"🧠 Planner: picking a '{category}' topic for {day}...")
    topic = _call_llm(prompt)
    topic = topic.strip('"\'').strip()

    return {
        "day": day,
        "category": category,
        "style": style,
        "niche": niche,
        "topic": topic,
    }


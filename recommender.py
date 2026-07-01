import json
import os
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - optional dependency
    genai = None

from spotify_search import SpotifySearcher

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def _configure_genai(api_key: Optional[str] = None) -> str:
    key = (api_key or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not key:
        raise ValueError("GOOGLE_API_KEY is not set")
    if genai is None:
        raise ImportError("google-generativeai is not installed")
    genai.configure(api_key=key)
    return key


def _extract_json_payload(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    cleaned = text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0]
    return json.loads(cleaned)


def build_search_query(intent: Dict[str, Any]) -> str:
    parts: List[str] = []
    if intent.get("artist"):
        parts.append(str(intent["artist"]))
    if intent.get("genre"):
        parts.append(str(intent["genre"]))
    if intent.get("mood"):
        parts.append(str(intent["mood"]))
    if intent.get("activity"):
        parts.append(str(intent["activity"]))
    if intent.get("language"):
        parts.append(str(intent["language"]))
    return " ".join(parts).strip() or "popular"


def extract_intent(requirement: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Ask Gemini to convert a natural-language requirement into a structured intent."""
    _configure_genai(api_key)
    prompt = f"""
You are a music intent extractor.
Convert the user's request into a compact JSON object.

User request: {requirement}

Return JSON only with this schema:
{{
  "mood": "short mood label",
  "genre": "primary genre",
  "activity": "activity or context",
  "artist": "artist if mentioned else null",
  "language": "language if mentioned else null",
  "energy": "low|medium|high",
  "vibe": "short vibe description"
}}
"""
    model = genai.GenerativeModel(DEFAULT_MODEL)
    response = model.generate_content(prompt)
    payload = _extract_json_payload(response.text)
    return {
        "mood": payload.get("mood") or "",
        "genre": payload.get("genre") or "",
        "activity": payload.get("activity") or "",
        "artist": payload.get("artist") or "",
        "language": payload.get("language") or "",
        "energy": payload.get("energy") or "",
        "vibe": payload.get("vibe") or "",
    }


def recommend_music(requirement: str, api_key: Optional[str] = None, num_recommendations: int = 6) -> Dict[str, Any]:
    """Use Gemini as the agent and Spotify as the tool to recommend tracks."""
    try:
        intent = extract_intent(requirement, api_key=api_key)
    except Exception as exc:
        return {"error": str(exc)}

    searcher = SpotifySearcher()
    tracks = searcher.search_by_intent(intent, limit=max(num_recommendations, 8))

    if not tracks:
        fallback_query = build_search_query(intent)
        tracks = searcher.search_tracks(fallback_query, limit=max(num_recommendations, 8))

    unique_tracks: List[Dict[str, Any]] = []
    seen_ids = set()
    for track in tracks:
        track_id = track.get("id")
        if track_id and track_id not in seen_ids:
            seen_ids.add(track_id)
            unique_tracks.append(track)
        if len(unique_tracks) >= num_recommendations:
            break

    reasoning = (
        f"The agent inferred a {intent.get('mood') or 'music'} mood, "
        f"{intent.get('genre') or 'genre'}-leaning vibe, and a {intent.get('activity') or 'general'} setting."
    )

    return {
        "requirement": requirement,
        "intent": intent,
        "reasoning": reasoning,
        "tracks": unique_tracks,
        "search_query": build_search_query(intent),
    }


def create_playlist(requirement: str, api_key: Optional[str] = None, playlist_size: int = 10) -> Dict[str, Any]:
    """Create a short playlist-style summary from the requirement."""
    try:
        intent = extract_intent(requirement, api_key=api_key)
    except Exception as exc:
        return {"error": str(exc)}

    searcher = SpotifySearcher()
    tracks = searcher.search_by_intent(intent, limit=max(playlist_size, 10))

    if not tracks:
        fallback_query = build_search_query(intent)
        tracks = searcher.search_tracks(fallback_query, limit=max(playlist_size, 10))

    return {
        "playlist_name": f"{intent.get('mood', 'Mood')} Flow",
        "description": f"A {intent.get('genre', 'music')} playlist for {intent.get('activity', 'your vibe')}",
        "tracks": tracks[:playlist_size],
    }

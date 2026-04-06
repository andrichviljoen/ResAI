from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, List


SYSTEM_PROMPT = """You are an actuarial reserving reviewer. Use only numbers in provided JSON context.
Never invent figures. Separate facts from interpretation and include uncertainty notes."""


def build_ai_context(state: Dict) -> Dict:
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "triangle_summary": state.get("triangle_summary", {}),
        "diagnostics": state.get("diagnostics", []),
        "reserve_outputs": state.get("reserve_outputs", {}),
        "selected_factors": state.get("selected_factors", {}),
        "user_overrides": state.get("user_overrides", {}),
    }


def prompt_for_mode(mode: str, user_query: str | None = None) -> str:
    base = {
        "summary": "Summarize the triangle diagnostics and reserve position in bullet points.",
        "challenge": "Challenge assumptions and factor selections; identify key risks and alternatives.",
        "report": "Draft concise management commentary with facts then interpretation.",
    }.get(mode, "Respond to the actuarial question based on context.")
    return f"{base}\nUser query: {user_query or 'N/A'}"


def run_ai(mode: str, context: Dict, user_query: str | None = None) -> Dict:
    api_key = os.getenv("OPENAI_API_KEY")
    prompt = prompt_for_mode(mode, user_query)
    if not api_key:
        # Deterministic fallback when API key absent
        facts = {
            "diagnostic_count": len(context.get("diagnostics", [])),
            "reserve_keys": list(context.get("reserve_outputs", {}).keys()),
        }
        text = (
            "FACTS:\n"
            f"- Diagnostics flagged: {facts['diagnostic_count']}\n"
            f"- Reserve output sections: {', '.join(facts['reserve_keys']) or 'none'}\n"
            "INTERPRETATION:\n"
            "- Configure OPENAI_API_KEY for richer commentary."
        )
        return {"mode": mode, "prompt": prompt, "response": text, "evidence": facts}

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(context, default=str)},
            {"role": "user", "content": prompt},
        ],
    )
    return {
        "mode": mode,
        "prompt": prompt,
        "response": completion.choices[0].message.content,
        "evidence": {
            "diagnostics_used": len(context.get("diagnostics", [])),
            "has_reserves": bool(context.get("reserve_outputs")),
        },
    }

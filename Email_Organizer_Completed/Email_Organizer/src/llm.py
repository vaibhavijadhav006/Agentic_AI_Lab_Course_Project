import os
import json
from typing import Optional


class LLMClient:
    """
    Optional LLM layer.

    If OPENAI_API_KEY is missing, the project uses local deterministic fallbacks.
    This keeps the educational project runnable without an API dependency.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception:
                self.client = None

    def text(self, prompt: str) -> Optional[str]:
        if not self.client:
            return None

        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt
            )
            return response.output_text
        except Exception:
            return None

    def classify(self, subject: str, body: str) -> Optional[dict]:
        prompt = f"""
Classify this faculty/college email.

Subject: {subject}
Body: {body}

Return ONLY valid JSON with:
{{
  "category": "academic|administrative|placement|meeting|information|other",
  "priority": "LOW|MEDIUM|HIGH|CRITICAL",
  "urgency_score": 0,
  "action_items": [],
  "follow_up_date": null,
  "reply_required": false,
  "reason": "short explanation"
}}

urgency_score must be 0-100.
"""
        raw = self.text(prompt)
        if not raw:
            return None

        try:
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                raw = raw.rsplit("```", 1)[0]
            return json.loads(raw)
        except Exception:
            return None

    def draft_reply(self, sender: str, subject: str, body: str, context: str = "") -> Optional[str]:
        prompt = f"""
Draft a short professional faculty email reply.

From: {sender}
Subject: {subject}
Original email:
{body}

Relevant previous context:
{context}

Rules:
- polite and concise
- do not invent facts
- do not claim an action was completed unless the original email says so
- return only the email body
"""
        return self.text(prompt)

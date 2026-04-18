from __future__ import annotations

import os

from openai import OpenAI


SYSTEM_PROMPT = """You are a technical writer summarizing a schema impact report.
Rewrite ONLY the prose explanation sections to be more readable.
DO NOT change: asset names, severity labels, confidence values, impact counts, dependency paths, or recommended actions.
Return only improved markdown. Do not add new facts."""


class LLMSummarizer:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY must be set for LLMSummarizer")
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def summarize(self, report_json: dict, markdown: str) -> str:
        prompt = f"IMPACT REPORT JSON:\n{report_json}\n\nCURRENT MARKDOWN:\n{markdown}"
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        content = resp.choices[0].message.content
        return content or markdown

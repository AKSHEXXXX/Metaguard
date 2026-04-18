from __future__ import annotations

import os

from openai import OpenAI


SYSTEM_PROMPT = """You are a technical writer summarizing a schema impact report.
Rewrite ONLY the prose explanation sections to be more readable.
DO NOT change: asset names, severity labels, confidence values, impact counts, dependency paths, or recommended actions.
Return only improved markdown. Do not add new facts."""


class LLMSummarizer:
    def __init__(self) -> None:
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()

        if groq_key:
            self.client = OpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        elif openai_key:
            self.client = OpenAI(api_key=openai_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        else:
            raise RuntimeError("Neither GROQ_API_KEY nor OPENAI_API_KEY is set for LLMSummarizer")

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

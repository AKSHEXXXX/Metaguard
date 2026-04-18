from __future__ import annotations

import os

from openai import OpenAI


SYSTEM_PROMPT = """You are a concise technical reviewer summarizing a schema impact report for a GitHub PR comment.

Rules:
- Keep the short title line (emoji + MetaGuard + severity label). Do not expand it.
- Keep the impact table exactly as-is — do not modify asset names, severity labels, or confidence values.
- In "Why this changed", use short flow lines like: `table_a` → `table_b`. Do not add verbose explanations.
- In "Changes detected", list each schema change in one line. Do not editorialize.
- In "Suggested follow-up", keep bullets short, specific, and actionable.
- Do NOT add new facts, asset names, or severity levels that are not in the original.
- Do NOT add preambles like "Here is the improved version". Return ONLY the improved markdown.
- The output should read like a reviewer note, not a generated audit log."""


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

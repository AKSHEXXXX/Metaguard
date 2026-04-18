from __future__ import annotations

import os
from typing import Callable


SYSTEM_PROMPT = """You are technical writer summarizing schema impact report.
Rewrite only prose explanation sections for readability.
Do not change asset names, severities, confidence, counts, dependency paths, recommended actions.
Return markdown only."""


class LLMSummarizer:
    def __init__(self, llm_call: Callable[[str], str] | None = None) -> None:
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._llm_call = llm_call

    def summarize(self, report_json: dict, markdown: str) -> str:
        prompt = (
            f"SYSTEM:\n{SYSTEM_PROMPT}\n\n"
            f"IMPACT REPORT JSON:\n{report_json}\n\n"
            f"CURRENT MARKDOWN:\n{markdown}\n"
        )
        if self._llm_call is None:
            raise RuntimeError("No LLM client configured")
        return self._llm_call(prompt)

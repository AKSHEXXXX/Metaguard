from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable


class SummaryValidationError(ValueError):
    pass


_BACKTICK_RE = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class LLMSummarizer:
    """
    Phase 4 summarizer wrapper.

    Contract:
    - Accepts full ImpactReport JSON (dict) + a deterministic markdown string.
    - Returns improved prose section only (wrapped in a bounded block).
    - Validates that the LLM output does not introduce new asset names when mentioned in backticks.
    - If validation fails, fall back to the deterministic markdown.
    """

    llm_call: Callable[[str], str]

    START = "<!-- metaguard-llm-summary:start -->"
    END = "<!-- metaguard-llm-summary:end -->"

    def apply(self, *, report: dict[str, Any], base_markdown: str) -> str:
        prompt = self._build_prompt(report=report)
        try:
            summary = self.llm_call(prompt)
        except Exception:
            return base_markdown

        try:
            cleaned = self._validate_and_clean(summary=summary, report=report)
        except SummaryValidationError:
            return base_markdown

        block = "\n".join(
            [
                self.START,
                "### Summary",
                cleaned.strip(),
                self.END,
                "",
            ]
        )
        return base_markdown.rstrip() + "\n\n" + block

    def _build_prompt(self, *, report: dict[str, Any]) -> str:
        # Keep the prompt deterministic and purely based on the report facts.
        # Important: require asset mentions to be backticked so we can validate.
        return (
            "Write a short PR-friendly prose summary (2-4 sentences) of the impact report below.\n"
            "Rules:\n"
            "- Do NOT introduce any new asset names.\n"
            "- If you mention an asset name, wrap it in backticks exactly (e.g., `stg_customers`).\n"
            "- Do NOT change severities, counts, or confidence.\n"
            "- Do NOT include tables.\n\n"
            f"ImpactReport JSON:\n{report}\n"
        )

    def _validate_and_clean(self, *, summary: str, report: dict[str, Any]) -> str:
        if not isinstance(summary, str):
            raise SummaryValidationError("LLM output must be a string")

        s = summary.strip()
        if not s:
            raise SummaryValidationError("LLM output is empty")

        allowed_assets = {r.get("asset_name") for r in report.get("records", []) if isinstance(r, dict)}
        allowed_assets = {a for a in allowed_assets if isinstance(a, str) and a}

        for m in _BACKTICK_RE.findall(s):
            if m not in allowed_assets:
                raise SummaryValidationError(f"Unknown asset mentioned: {m}")

        return s


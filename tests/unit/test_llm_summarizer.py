from __future__ import annotations

import pytest

from src.llm.summarizer import LLMSummarizer


def test_llm_summarizer_calls_llm_with_prompt() -> None:
    captured: dict[str, str] = {}

    def fake_llm(prompt: str) -> str:
        captured["prompt"] = prompt
        return "ok"

    out = LLMSummarizer(llm_call=fake_llm).summarize(report_json={"id": "F1"}, markdown="md")
    assert out == "ok"
    assert "IMPACT REPORT JSON" in captured["prompt"]


def test_llm_summarizer_raises_without_client() -> None:
    with pytest.raises(RuntimeError):
        LLMSummarizer().summarize(report_json={"id": "F1"}, markdown="md")

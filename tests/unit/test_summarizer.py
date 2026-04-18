from __future__ import annotations

from src.engine.summarizer import LLMSummarizer


def test_summarizer_appends_llm_summary_when_valid() -> None:
    report = {
        "id": "F1",
        "highest_severity": "CRITICAL",
        "total_affected": 1,
        "records": [
            {"asset_name": "stg_customers"},
        ],
    }

    def llm_call(_prompt: str) -> str:
        return "This change may break downstream consumers like `stg_customers`; please coordinate before merge."

    base = "## MetaGuard\n"
    out = LLMSummarizer(llm_call=llm_call).apply(report=report, base_markdown=base)

    assert "metaguard-llm-summary:start" in out
    assert "`stg_customers`" in out


def test_summarizer_falls_back_when_hallucinated_asset_is_mentioned() -> None:
    report = {
        "id": "F1",
        "highest_severity": "CRITICAL",
        "total_affected": 1,
        "records": [
            {"asset_name": "stg_customers"},
        ],
    }

    def llm_call(_prompt: str) -> str:
        return "This impacts `fake_asset`."

    base = "## MetaGuard\n"
    out = LLMSummarizer(llm_call=llm_call).apply(report=report, base_markdown=base)
    assert out == base


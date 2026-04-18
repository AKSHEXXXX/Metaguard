from __future__ import annotations

from src.llm.validator import SummaryValidator


def test_validator_passes_when_assets_and_severity_present() -> None:
    report = {
        "records": [
            {"asset_name": "stg_customers", "severity": "CRITICAL"},
            {"asset_name": "mart_customers", "severity": "HIGH"},
        ]
    }
    summary = "Impact on stg_customers CRITICAL and mart_customers HIGH."
    assert SummaryValidator().validate(report, summary) is True


def test_validator_fails_when_asset_missing() -> None:
    report = {"records": [{"asset_name": "stg_customers", "severity": "CRITICAL"}]}
    summary = "Only CRITICAL mentioned."
    assert SummaryValidator().validate(report, summary) is False

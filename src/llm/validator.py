from __future__ import annotations


class SummaryValidator:
    def validate(self, report_json: dict, summary: str) -> bool:
        records = report_json.get("records", [])
        if not isinstance(records, list):
            return False
        for record in records:
            if not isinstance(record, dict):
                return False
            asset_name = record.get("asset_name")
            severity = record.get("severity")
            if isinstance(asset_name, str) and asset_name and asset_name not in summary:
                return False
            if isinstance(severity, str) and severity and severity not in summary:
                return False
        return True

from __future__ import annotations

from src.domain.enums import ChangeType, Severity
from src.domain.models import ImpactReport, SchemaChange


def _severity_badge(sev: Severity) -> str:
    if sev is Severity.CRITICAL:
        return "🔴"
    if sev is Severity.HIGH:
        return "🟠"
    if sev is Severity.MEDIUM:
        return "🟡"
    return "🟢"


def _severity_label(sev: Severity) -> str:
    return {
        Severity.CRITICAL: "critical",
        Severity.HIGH: "high-impact",
        Severity.MEDIUM: "moderate",
        Severity.LOW: "low-risk",
    }[sev]


def _change_verb(ct: ChangeType) -> str:
    return {
        ChangeType.DROP_COLUMN: "dropped column",
        ChangeType.RENAME_COLUMN: "renamed column",
        ChangeType.ALTER_TYPE: "changed column type",
        ChangeType.ALTER_NULLABILITY: "changed nullability",
        ChangeType.ADD_COLUMN: "added column",
        ChangeType.UNKNOWN: "modified",
    }.get(ct, "modified")


def _suggested_followup(sev: Severity) -> list[str]:
    if sev is Severity.CRITICAL:
        return [
            "Confirm downstream assets explicitly use the affected column before merging.",
            "Add a compatibility alias or view layer if possible.",
            "Coordinate with downstream asset owners.",
        ]
    if sev is Severity.HIGH:
        return [
            "Review the downstream query definitions for the affected field.",
            "Run integration tests for the impacted assets.",
            "Notify the asset owners if this change is intentional.",
        ]
    if sev is Severity.MEDIUM:
        return [
            "Check for strict schema consumers that may reject the change.",
            "Run validation queries post-deploy.",
        ]
    return [
        "No immediate action required — monitor for unexpected errors after deploy.",
    ]


class PRCommentRenderer:
    @staticmethod
    def render(report: ImpactReport, changes: list[SchemaChange] | None = None) -> str:
        badge = _severity_badge(report.highest_severity)
        label = _severity_label(report.highest_severity)
        # Template: 🟠 MetaGuard found a high-impact schema change
        title = f"{badge} MetaGuard found a {label} schema change"

        n = report.total_affected
        # Template: This PR affects 3 downstream assets.
        summary = f"This PR affects {n} downstream asset{'s' if n != 1 else ''}."

        lines: list[str] = [title, "", summary, ""]

        # --- Impact table ---
        include_owner = any(r.owner for r in report.records)
        if include_owner:
            lines.append("| Asset | Owner | Type | Severity | Confidence |")
            lines.append("| --- | --- | --- | --- | --- |")
        else:
            lines.append("| Asset | Type | Severity | Confidence |")
            lines.append("| --- | --- | --- | --- |")

        for r in report.records:
            if include_owner:
                owner = r.owner or "—"
                lines.append(f"| `{r.asset_name}` | {owner} | {r.asset_type.value} | {r.severity.value} | {r.confidence.value} |")
            else:
                lines.append(f"| `{r.asset_name}` | {r.asset_type.value} | {r.severity.value} | {r.confidence.value} |")

        # --- Why this changed ---
        if report.records:
            lines.append("")
            lines.append("Why this changed:")
            # Use a set to deduplicate flow pairs across multiple affected assets
            flow_pairs: set[str] = set()
            for r in report.records:
                if r.path and len(r.path) >= 2:
                    for i in range(len(r.path) - 1):
                        pair = f"- `{r.path[i]}` flows into `{r.path[i+1]}`"
                        flow_pairs.add(pair)
            
            for pair in sorted(list(flow_pairs)):
                lines.append(pair)

        # Note: 'Changes detected' section is removed to follow the target template strictly.

        # --- Suggested follow-up ---
        lines.append("")
        lines.append("Suggested follow-up:")
        for a in _suggested_followup(report.highest_severity):
            lines.append(f"- {a}")

        return "\n".join(lines).strip() + "\n"

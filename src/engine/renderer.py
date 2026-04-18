from __future__ import annotations

from src.domain.enums import Severity
from src.domain.models import ImpactReport


def _severity_badge(sev: Severity) -> str:
    if sev is Severity.CRITICAL:
        return "🔴"
    if sev is Severity.HIGH:
        return "🟠"
    if sev is Severity.MEDIUM:
        return "🟡"
    return "🟢"


def _recommended_actions(sev: Severity) -> list[str]:
    if sev is Severity.CRITICAL:
        return [
            "Confirm downstream assets explicitly use the affected column before merging",
            "Add a compatibility alias or view layer",
            "Coordinate with downstream owners",
            "Consider staged deprecation",
        ]
    if sev is Severity.HIGH:
        return [
            "Review downstream query definitions for the affected field",
            "Run integration tests covering affected assets",
            "Notify asset owners listed in metadata",
        ]
    if sev is Severity.MEDIUM:
        return [
            "Check for strict schema consumers",
            "Run validation queries post-deploy",
        ]
    return [
        "No immediate action required",
        "Monitor for unexpected errors after deploy",
    ]


class PRCommentRenderer:
    @staticmethod
    def render(report: ImpactReport) -> str:
        badge = _severity_badge(report.highest_severity)
        title = f"## {badge} MetaGuard — {report.highest_severity.value} Impact Detected"

        summary = f"{report.total_affected} downstream assets affected"

        lines: list[str] = [title, "", summary, ""]

        include_owner = any(r.owner for r in report.records)
        if include_owner:
            lines.append("| Asset | Owner | Type | Severity | Confidence | Reason |")
            lines.append("|-------|-------|------|----------|------------|--------|")
        else:
            lines.append("| Asset | Type | Severity | Confidence | Reason |")
            lines.append("|-------|------|----------|------------|--------|")
        for r in report.records:
            if include_owner:
                owner = r.owner or "-"
                lines.append(
                    f"| {r.asset_name} | {owner} | {r.asset_type.value} | {r.severity.value} | {r.confidence.value} | {r.reason} |"
                )
            else:
                lines.append(
                    f"| {r.asset_name} | {r.asset_type.value} | {r.severity.value} | {r.confidence.value} | {r.reason} |"
                )

        if report.records:
            lines.append("")
            lines.append("Dependency paths:")
            for r in report.records:
                if r.path:
                    lines.append(f"- **{r.asset_name}**: " + " → ".join(r.path))

        lines.append("")
        lines.append("Recommended actions:")
        for a in _recommended_actions(report.highest_severity):
            lines.append(f"- {a}")

        return "\n".join(lines).strip() + "\n"

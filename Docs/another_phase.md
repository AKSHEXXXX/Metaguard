# MetaGuard Phase 2 Plan

## Goal
Polish the PR bot comment first, then move through severity tuning, multi-change PR testing, and column-level lineage so the demo looks human, credible, and complete.

## Phase 1 — Polish the bot comment

The current bot output is technically correct but too stiff, repetitive, and report-like. The goal is to make it sound like a concise reviewer note rather than a generated audit log.

### Target style
- Start with a short one-line summary.
- Keep the impact table, but avoid extra explanation before and after it.
- Replace formal phrases like “A total of 3 downstream assets have been affected” with simpler language like “This PR affects 3 downstream assets.”
- Rename sections to feel natural, for example:
  - `Why this changed`
  - `Suggested follow-up`
- Keep recommendations short, specific, and tied to the change type.

### Suggested comment template
```md
🟠 MetaGuard found a high-impact schema change

This PR affects 3 downstream assets.

| Asset | Type | Severity | Confidence |
| --- | --- | --- | --- |
| ... | TABLE | HIGH | MEDIUM |
| ... | TABLE | HIGH | MEDIUM |
| ... | TABLE | HIGH | MEDIUM |

Why this changed:
- `fact_orders` flows into `product_performance`
- `fact_orders` flows into `customer_metrics`
- `customer_metrics` flows into `executive_sales_summary`

Suggested follow-up:
- Review the downstream query definitions for the affected field.
- Run integration tests for the impacted assets.
- Notify the asset owners if this change is intentional.
```

### Renderer changes to make
- Shorten the title.
- Remove duplicate lead-in sentences.
- Trim the explanation around the table.
- Replace generic “To address the issue” text with a shorter “Suggested follow-up”.
- Keep the output readable in GitHub dark mode.

## Phase 2 — Severity tuning

Once the comment reads naturally, tune the rules engine so the severity labels match the actual impact more closely. The current `CRITICAL` vs `WARNING` split should reflect how many downstream assets are hit, how deep the lineage path is, and whether the change is destructive or additive.

### What to check
- A direct breaking change on a leaf asset should stay high severity.
- A shallow non-breaking change should not look as severe as a multi-hop destructive change.
- Confidence values should not overstate certainty when lineage is partial.

### What to adjust
- Severity thresholds in the rules engine.
- Weighting for destructive changes like drop/rename/type change.
- Penalties or boosts based on lineage depth.
- Confidence scoring when lineage is sparse or inferred.

### Output you want
- `CRITICAL` only for real high-risk cases.
- `HIGH` for meaningful downstream disruption.
- `WARNING` for lower-risk or partial-impact changes.
- The LLM comment should mirror the final computed severity instead of exaggerating it.

## Phase 3 — Multi-change PRs

After severity is calibrated, test a migration with 3–4 simultaneous changes. This verifies that the engine groups and reports multiple changes cleanly instead of flattening them into one noisy block.

### Test case
Use one migration file that includes a mix of changes, for example:
- one `DROP COLUMN`
- one `RENAME COLUMN`
- one `ALTER COLUMN TYPE`
- one additive change if needed for contrast

### What to verify
- Each change is detected separately.
- The report groups affected assets by change, not just by file.
- Duplicate downstream hits are deduplicated or clearly aggregated.
- The PR comment still reads cleanly when multiple changes are present.

### Expected outcome
The report should show:
- a short summary of total changes,
- grouped impacts,
- per-change severity,
- and a concise recommendation block.

## Phase 4 — Column-level lineage

After table-level lineage works, add column-level edges to the seed script so the demo can show field-specific impact. This makes the PR comment more believable because it can explain which column actually caused the downstream effect.

### What to seed
- A real upstream table to downstream table edge.
- A column mapping for one or more important fields.
- At least one example where a column change propagates through lineage.

### What to verify
- The lineage renderer can show column-specific dependency paths.
- The impact report names the changed column, not just the table.
- The PR comment explains the consequence in plain language.

### Why this matters
Column-level lineage makes the system feel more precise and less generic. It also gives you a stronger demo because reviewers can see the exact field that triggered the impact.

## Execution order

Follow this order so you do not introduce noise too early:
1. Polish the PR comment renderer.
2. Tune severity thresholds.
3. Run the multi-change PR stress test.
4. Add column-level lineage to the seeded sandbox.
5. Re-run the smoke test and PR demo with the improved output.

## Acceptance criteria
- The PR comment sounds human and concise.
- Severity labels match the real risk level.
- Multi-change migrations are reported cleanly.
- Column-level lineage appears in the final demo.
- The output is good enough to show in a submission without extra explanation.

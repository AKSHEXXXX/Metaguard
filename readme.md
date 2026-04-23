# MetaGuard 🛡️

> **Catch breaking schema changes before they catch you.**

MetaGuard is a schema impact analysis engine that lives inside your CI/CD
pipeline. The moment a pull request touches a SQL migration file, MetaGuard
automatically traverses your entire downstream data lineage graph — across
tables, views, dashboards, and ML models — and posts a precise, human-readable
impact report directly on the PR. No Slack pings, no post-mortems, no 3 AM
incidents. Just a comment that tells your team exactly what will break and why,
before the merge button is pressed.


---

## The Problem

A data engineer drops a column. It looked safe. The table had no obvious
dependents. Forty-eight hours later, three dashboards are blank, a downstream
ML feature pipeline silently starts returning nulls, and the on-call engineer
is bisecting git history at midnight.

This happens because **schema changes are blind**. There is no standard place
in a developer's workflow that answers the question: *"If I change this column,
what downstream assets will break?"*

MetaGuard answers that question at the exact right moment — inside the pull
request, before anything is merged.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Your GitHub Repository                        │
│                                                                      │
│   Developer opens PR with migrations/002_alter_orders.sql           │
│                              │                                       │
│                              ▼                                       │
│            ┌─────────────────────────────┐                          │
│            │     GitHub Actions Trigger   │                          │
│            │  (on: pull_request, paths:   │                          │
│            │   migrations/*.sql)          │                          │
│            └─────────────┬───────────────┘                          │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
                           ▼
          ┌────────────────────────────────┐
          │        MetaGuard Engine        │
          │                                │
          │  1. SQL Parser                 │
          │     Detects: DROP COLUMN,      │
          │     ALTER TYPE, RENAME, etc.   │
          │                                │
          │  2. Metadata Provider          │
          │     Queries OpenMetadata via   │
          │     MCP or REST API to fetch   │
          │     full downstream lineage    │
          │                                │
          │  3. Impact Rules Engine        │
          │     Scores severity +          │
          │     confidence per asset.      │
          │     Penalizes deep hops with   │
          │     no column-level map.       │
          │                                │
          │  4. Report Builder             │
          │     Generates markdown with    │
          │     severity table, lineage    │
          │     chain, and action items.   │
          └──────────────┬─────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │     OpenMetadata Sandbox     │
          │                              │
          │  MCP Server / REST API       │
          │  Returns: lineage graph,     │
          │  column maps, asset owners,  │
          │  governance tags             │
          └──────────────┬───────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │      GitHub PR Comment       │
          │                              │
          │  🔴 MetaGuard CRITICAL       │
          │  3 downstream assets at risk │
          │  [impact table]              │
          │  [lineage chain]             │
          │  [suggested follow-up]       │
          └──────────────────────────────┘
```

The entire pipeline runs in under 60 seconds. Developers never leave GitHub.

---

## Example Output

When MetaGuard detects a destructive schema change, it posts this directly
on your PR:

---

🔴 **MetaGuard CRITICAL** — This PR affects 3 downstream assets.

| Asset | Type | Severity | Confidence |
|-------|------|----------|------------|
| `acme_nexus_analytics.ANALYTICS.METRICS.product_performance` | TABLE | CRITICAL | MEDIUM |
| `acme_nexus_analytics.ANALYTICS.METRICS.customer_metrics` | TABLE | CRITICAL | MEDIUM |
| `acme_nexus_redshift.enterprise_dw.public.executive_sales_summary` | TABLE | CRITICAL | MEDIUM |

**Why this changed:**
- `fact_orders` → `customer_metrics`
- `fact_orders` → `product_performance`
- `customer_metrics` → `executive_sales_summary`

**Changes detected:**
- Column-level lineage missing for `product_performance` — confidence penalized
- Column-level lineage missing for `customer_metrics` — confidence penalized

**Suggested follow-up:**
- Confirm downstream assets explicitly use the affected column before merging
- Add a compatibility alias or view layer if possible
- Coordinate with downstream asset owners before this PR is approved

---

## Features

**Severity Tuning**
Calibrates risk levels (`CRITICAL`, `HIGH`, `WARNING`, `LOW`) based on
the nature of the change and lineage depth. Avoids alert fatigue by only
escalating when the blast radius is real.

**Multi-Change PR Stress Testing**
Handles complex migrations with multiple concurrent schema changes in a
single PR — grouping, deduplicating, and ranking them cleanly.

**Column-Level Lineage**
Traces exact column dependencies. A table that uses an upstream asset
but doesn't reference the changed column will not trigger a false positive.

**Confidence Scoring**
Penalizes confidence for deep lineage hops where no column map exists.
Tells you not just *what* might break but *how certain* MetaGuard is.

**Graceful Fallback**
If the OpenMetadata sandbox is unreachable, MetaGuard falls back to
fixture-based mock mode automatically — the action never fails silently.

**Optional LLM Summarizer**
With an OpenAI or Groq key configured, MetaGuard appends a conversational
plain-English summary to the report — useful for non-technical reviewers.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Core engine | Python 3.11+ |
| Metadata & lineage | OpenMetadata (MCP + REST API) |
| CI/CD integration | GitHub Actions |
| PR commenting | GitHub REST API |
| Optional LLM layer | OpenAI / Groq |

---

## Quick Start

### Use MetaGuard in your repo (2 minutes)

Create `.github/workflows/metaguard.yml`:

```yaml
name: MetaGuard Schema Impact Analysis

on:
  pull_request:
    types: [opened, synchronize, reopened]
    paths:
      - "migrations/*.sql"
      - "models/**/*.sql"
      - "schema/**/*.sql"

permissions:
  contents: read
  pull-requests: write

jobs:
  metaguard:
    name: Run MetaGuard
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install -r requirements.txt

      - name: Run MetaGuard
        env:
          OPENMETADATA_HOST: ${{ secrets.OPENMETADATA_HOST }}
          OPENMETADATA_TOKEN: ${{ secrets.OPENMETADATA_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python main.py \
            --mode sandbox \
            --transport mcp \
            --om-asset "your.entity.fqn" \
            --pr-number "${{ github.event.pull_request.number }}" \
            --repo "${{ github.repository }}" \
            --output github
```

Add your secrets under **Settings → Secrets → Actions** in your repo.
That's it. MetaGuard will run on every PR that touches a SQL file.

---

### Run locally

```bash
git clone https://github.com/AKSHEXXXX/Metaguard.git
cd Metaguard

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
# fill in your values in .env

# test with mock fixture (no OpenMetadata needed)
python main.py --mode mock --changed-files F1

# test against live OpenMetadata sandbox
python main.py \
  --mode sandbox \
  --transport mcp \
  --om-asset "acme_nexus_analytics.ANALYTICS.MARTS.fact_orders"
```

---

## Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENMETADATA_HOST` | OpenMetadata instance URL | `https://sandbox.open-metadata.org` |
| `OPENMETADATA_TOKEN` | JWT Personal Access Token | `eyJraWQiOi...` |
| `OPENMETADATA_MCP_URL` | MCP server endpoint | `https://sandbox.open-metadata.org/mcp` |
| `LINEAGE_MAX_DEPTH` | Max lineage hops to traverse | `5` |
| `HTTP_TIMEOUT_SECONDS` | External API timeout | `30` |
| `LOG_LEVEL` | Verbosity (`DEBUG`, `INFO`, `WARNING`) | `INFO` |
| `GITHUB_TOKEN` | Token for posting PR comments | `ghp_abc123...` |
| `GITHUB_REPOSITORY` | Target repo in `owner/repo` format | `AKSHEXXXX/Metaguard` |
| `ENABLE_LLM_SUMMARY` | Enable LLM plain-English summary | `true` |
| `OPENAI_API_KEY` | OpenAI key for LLM summarizer | `sk-...` |
| `GROQ_API_KEY` | Groq key for LLM summarizer | `gsk_...` |

---

## Demo Video of the Project

You can see the working of the project here:

https://www.loom.com/share/9420193d7307460daa307edbba4395de



---

## Project Structure

```
Metaguard/
├── main.py                  # Entry point
├── requirements.txt
├── .env.example
├── .github/
│   └── workflows/
│       └── metaguard.yml    # GitHub Actions workflow
├── core/
│   ├── parser.py            # SQL change parser
│   ├── analyzer.py          # Core impact engine
│   ├── rules.py             # ImpactRulesEngine
│   └── reporter.py          # Markdown report builder
├── providers/
│   ├── openmetadata.py      # MCP + REST API client
│   └── mock.py              # Fixture-based mock provider
├── adapters/
│   └── github.py            # GitHub PR comment adapter
├── fixtures/                # Test fixture data (F1, F2, ...)
└── tests/
    └── test_analyzer.py
```

---

## License

MIT

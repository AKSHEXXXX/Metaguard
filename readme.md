# MetaGuard

MetaGuard is a schema impact analysis engine that automatically detects downstream breakage risks caused by database schema changes (like dropping or renaming columns). Integrated directly into your CI/CD pipeline, it parses incoming pull requests containing SQL migrations, traverses the data lineage graph, and leaves a concise, human-readable comment summarizing the potential blast radius. This matters because it shifts data quality checks to the left, preventing breaking changes from reaching production and breaking downstream pipelines, dashboards, or machine learning models.

## Architecture Overview

The system operates through three primary components working in concert:
1. **Core Analyzer**: Parses SQL migration files from the PR to identify exact changes (e.g., `DROP COLUMN legacy_id`).
2. **Metadata Provider (OpenMetadata Sandbox)**: Takes the affected entity and queries the OpenMetadata sandbox via a Model Context Protocol (MCP) server or REST API to fetch downstream table and column-level lineage graphs.
3. **Rules & Report Engine**: The ImpactRulesEngine evaluates the depth and nature of the change (e.g., incompatible type changes, column removal) to assign a calibrated severity and confidence score. Finally, the report builder and PR renderer format the findings and post them back to GitHub.

## Features

- **Severity Tuning**: Accurately calibrates risk levels (`CRITICAL`, `HIGH`, `WARNING`, `LOW`) based on the nature of the change and lineage depth, avoiding alert fatigue.
- **Multi-Change PR Stress Testing**: Gracefully handles and groups complex migrations containing multiple concurrent schema changes in a single PR.
- **Column-Level Lineage**: Traces exact column dependencies across tables, avoiding false positives where a table depends on an upstream asset but doesn't use the changed column.
- **Impact Scoring**: Calculates severity and confidence scores dynamically, penalizing confidence for deep, inferred lineage hops without column maps.
- **Markdown PR Report Generation**: Automatically posts a clean, highly readable markdown comment on GitHub PRs that developers can quickly parse without leaving their workflow.

## Tech Stack

- **Python 3.11+**: Core logic, parsing, and analysis.
- **OpenMetadata**: Data catalog providing the lineage graph.
- **MCP (Model Context Protocol)**: Efficient and standardized metadata transport.
- **GitHub Actions & REST API**: CI/CD integration and PR comment orchestration.
- **LLM Integrations (OpenAI / Groq)**: Optional summarizer for generating conversational PR notes.

## How to Run It Locally

Assuming you have `git` and `Python 3.11+` installed:

1. **Clone the repository**
   ```bash
   git clone https://github.com/AKSHEXXXX/Metaguard.git
   cd Metaguard
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Set up your environment**
   Create a `.env` file at the root of the project (see the Configuration section below) and fill in your secrets.

5. **Run the analyzer**
   To test it using a mock fixture locally:
   ```bash
   python main.py --mode mock --changed-files F1
   ```
   To run it against your OpenMetadata sandbox:
   ```bash
   python main.py --mode sandbox --transport mcp --om-asset "your.entity.fqn"
   ```

## Example Output

When a destructive schema change is detected, MetaGuard will comment on your PR with a report similar to this:

```md
🟠 MetaGuard found a high-impact schema change

This PR affects 3 downstream assets.

| Asset | Type | Severity | Confidence |
| --- | --- | --- | --- |
| `fact_orders` | TABLE | HIGH | HIGH |
| `product_performance` | VIEW | WARNING | MEDIUM |
| `executive_sales_summary` | DASHBOARD | WARNING | LOW |

Why this changed:
- `fact_orders` flows into `product_performance`
- `product_performance` flows into `executive_sales_summary`

Suggested follow-up:
- Review the downstream query definitions for the affected field.
- Run integration tests for the impacted assets.
- Notify the asset owners if this change is intentional.
```

## Configuration

MetaGuard uses the following environment variables. Set them in your local `.env` file or in your CI/CD secrets:

| Variable | Description | Example Value |
| --- | --- | --- |
| `OPENMETADATA_HOST` | The URL of your OpenMetadata instance. | `https://sandbox.open-metadata.org` |
| `OM_HOST` | Fallback alias for `OPENMETADATA_HOST`. | `https://sandbox.open-metadata.org` |
| `OPENMETADATA_TOKEN` | JWT token for authenticating with OpenMetadata. | `eyJraWQiOi...` |
| `OM_JWT_TOKEN` | Alias for `OPENMETADATA_TOKEN` used in authentication providers. | `eyJraWQiOi...` |
| `OPENMETADATA_MCP_URL` | URL for the OpenMetadata Model Context Protocol server. | `https://sandbox.open-metadata.org/mcp` |
| `LINEAGE_MAX_DEPTH` | Maximum number of hops to traverse down the lineage graph. | `5` |
| `HTTP_TIMEOUT_SECONDS` | Timeout duration for external API requests. | `30` |
| `LOG_LEVEL` | Application logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). | `INFO` |
| `SMOKE_FORCE_REST` | Forces the use of REST API over MCP in smoke tests if set to `true`. | `false` |
| `SMOKE_ENTITY_FQN` | Default fully qualified name to use during smoke testing. | `acme.analytics.fact_orders` |
| `GITHUB_TOKEN` | Token with permissions to post comments on Pull Requests. | `ghp_abc123...` |
| `GITHUB_REPOSITORY` | Format: `owner/repo`. Used by the GitHub adapter. | `AKSHEXXXX/Metaguard` |
| `GITHUB_API_URL` | Base URL for GitHub API (useful for GitHub Enterprise). | `https://api.github.com` |
| `ENABLE_LLM_SUMMARY` | If `true`, enables LLM-generated summaries for the PR comment. | `true` |
| `OPENAI_API_KEY` | API key if using OpenAI for LLM summaries. | `sk-...` |
| `GROQ_API_KEY` | API key if using Groq for LLM summaries. | `gsk_...` |
# MetaGuard — Product Requirements Document

## Overview

MetaGuard is an AI-assisted schema change impact analyzer. It detects risky schema changes in pull requests, resolves downstream asset dependencies from metadata and lineage graphs, computes impact severity, and posts a structured human-readable summary back to the PR before merge.

## Problem Statement

Data teams frequently change schemas without awareness of downstream impact. A dropped or renamed column can silently break dashboards, dbt models, ETL pipelines, and ML feature stores. Existing PR review flows have no lineage-aware guardrail. Developers discover breakage only after merge and deployment.

## Users

- Data engineers making schema changes in SQL migrations or dbt models
- Analytics engineers reviewing PRs against shared data assets
- Platform and data governance teams enforcing change policies
- Hackathon judges evaluating the demo

## Core User Story

As a developer opening a PR that modifies a table schema, I want an automated PR comment telling me which downstream assets are affected, why they are affected, and what I can do to reduce risk before merging.

## MVP Goals

The MVP must:
- Accept schema diff input (raw SQL, dbt model diff, or pre-normalized JSON)
- Parse and normalize changes into typed semantic events
- Load lineage and metadata from a provider (mock in Phase 1, real OpenMetadata in Phase 2)
- Traverse the downstream dependency graph
- Apply deterministic impact rules to compute severity and confidence
- Build a structured impact report
- Render a PR-ready markdown comment

## Non-Goals for MVP

- Full production governance enforcement
- All SQL dialects
- Complex multi-tenant auth management
- Real-time streaming observability
- Autonomous merge blocking in version 1

## Inputs

| Input | Source | Phase |
|-------|--------|-------|
| PR metadata | GitHub Action or CLI | Phase 1+ |
| Changed schema files | Git diff | Phase 1+ |
| Normalized change events | JSON fixture or parsed SQL | Phase 1 |
| Lineage graph | Mock provider | Phase 1 |
| Lineage graph | OpenMetadata API or MCP | Phase 2 |

## Outputs

| Output | Format | Phase |
|--------|--------|-------|
| Structured impact report | JSON | Phase 1 |
| PR comment markdown | Markdown string | Phase 1 |
| Risk score | Enum: low/medium/high/critical | Phase 1 |
| GitHub PR comment | GitHub API call | Phase 3 |

## Success Criteria

- Given a mocked DROP_COLUMN change, the engine correctly identifies all downstream affected assets via graph traversal
- The output includes asset name, type, severity, confidence, and dependency path
- The markdown PR comment is concise and credible
- Swapping mock provider for real OpenMetadata provider requires zero changes to core engine logic
- All 5 core fixture test scenarios pass before any external integration begins

## System Constraints

- Must support offline/local development without OpenMetadata VM
- Core engine must be deterministic and testable by fixtures
- LLM must only summarize — it cannot compute severity, confidence, or impact facts
- Must be hackathon-demo-ready with a 2-minute walkthrough

## Release Phases

| Phase | Scope |
|-------|-------|
| Phase 1 | Domain models, mock provider, traversal, rules, report, renderer, tests |
| Phase 2 | OpenMetadata provider, MCP client integration, JWT auth |
| Phase 3 | GitHub Action trigger, PR comment publisher, CI/CD integration |
| Phase 4 | LLM summarizer layer, merge block option, full demo polish |
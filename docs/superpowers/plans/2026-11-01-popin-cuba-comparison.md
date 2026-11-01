# POPIN Cuba Model Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Prepare a resumable, full-text comparison of decision models on the 519 Cuba `SPEECH` documents against POPIN v4.

**Architecture:** Read documents and baseline scores from `popin.duckdb` in read-only mode; send one full discourse per model request through OpenRouter; write results to a separate local DuckDB and exports. Keep prompt, ordinal answers, normalized scores, raw responses and failures auditable.

**Tech Stack:** Python, DuckDB, OpenRouter API, JSON.

**Spec:** `docs/superpowers/specs/2026-11-01-popin-v4-1-0-cuba-design.md`

## Global Constraints

- Use exactly the 519 Cuba records where `iso3='CUB'` and `dtype='SPEECH'`.
- Read the complete discourse text; do not silently truncate or chunk it.
- Preserve POPIN v4's six dimensions and prompt wording/rules as the basis for an explicit decision-model adaptation.
- Ask for integer levels 0–9 per dimension and normalize as `level * 100 / 9`; retain both values.
- Do not invoke model APIs automatically; do not edit the source DuckDB.
- Record unsupported context length or API errors as status rows and report paired baseline coverage.

## Review Focus

- Very long speeches or model context limits: record a clear skip/error, never truncate. Pin with a dry-run path that does not call the API.
- Existing output/resume behavior: do not repeat completed model/document pairs. Pin with a resume-only run against a prepared results database.
- Malformed/incomplete model JSON: retain raw output and an error status; do not emit fabricated scores.
- Missing POPIN baseline for a document: retain the model result but exclude it from paired statistics.
- API key/model configuration absent: show actionable setup instructions without exposing secrets.

---

### Task 1: Freeze the decision prompt and output contract

**Files:**
- Create: `decision_tests/cuba/README.md`
- Create: `decision_tests/cuba/prompt_v4_decision.md`

**Interfaces:**
- Produces: six dimension identifiers and 0–9 response schema matching the approved design; prompt source/hash recorded in every run.

- [ ] Copy the v4 measurement definitions and cue distinctions from `04_score.py`; add concise ordinal anchors and strict JSON schema, labeling the adaptation.
- [ ] Document one full-text request per model/document, output database path, OpenRouter model IDs, and how to start/resume manually.

### Task 2: Implement the Cuba comparison runner

**Files:**
- Create: `decision_tests/cuba/compare_cuba.py`

**Interfaces:**
- `load_cuba_documents(db_path: Path) -> list[dict]`
- `score_response(payload: str) -> dict`
- `run_comparison(db_path: Path, output_path: Path, models: list[str], dry_run: bool) -> None`

- [ ] Load exactly 519 source rows and corresponding POPIN v4 baseline scores from a read-only connection.
- [ ] Persist result schema with document/model ID, six ordinal and normalized scores, baseline vector, raw response, status, token/latency metadata, prompt hash and error.
- [ ] Implement API calls behind an explicit CLI flag; make dry run the default and keep completed pairs resumable.
- [ ] Generate paired-comparison CSV and per-model coverage/summary files from completed results.

### Task 3: Prepare a local, auditable dry run

**Files:**
- Modify: `decision_tests/cuba/README.md`

- [ ] Run only in dry-run mode; inspect that the queue contains 519 unique speeches and that complete text is selected without writing to `popin.duckdb`.
- [ ] Review the generated prompt hash, result schema, and documentation of ordinal normalization before leaving the tool ready for user execution.

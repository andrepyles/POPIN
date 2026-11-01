# POPIN Reproducible Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Complete GitHub release v4.1.0 with a clearly documented, downloadable research package sufficient to reproduce and audit POPIN v4.

**Architecture:** Keep source code, compact exports, manifests and reproduction instructions in Git. Publish the large analytical DuckDB as a release asset, distinguish it from the website database, and preserve v4.0's Qwen/chunked lineage separately from v4.1.0's GPT-5.6/full-text article snapshot.

**Tech Stack:** Python, DuckDB, CSV/Parquet, JSON manifests, GitHub CLI/release assets.

**Spec:** `docs/superpowers/specs/2026-11-01-popin-v4-1-0-cuba-design.md`

## Global Constraints

- Preserve POPIN v4 as the measurement instrument; label v4.1.0 as the package revision.
- Keep the frozen 45,492-document snapshot and identify 44,592 full-run and 900 pilot records by provenance; separate them if their protocol differs.
- Keep `popin.duckdb` read-only during package preparation; distinguish it from `06_website/popin_web.duckdb`.
- Do not add a large database to Git history; attach it as a release asset and publish SHA-256 hashes.
- Include complete source texts only within the corpus coverage already published in v4.0; preserve source and redistribution notes.
- Never publish `.env`, credentials, temporary caches, or transient logs.

## Review Focus

- Snapshot score provenance: establish whether the 900 pilot records used the same v4 full-text protocol; if not, separate and regenerate primary analysis outputs.
- Database identity: ensure users can tell the full research DB from the small website DB by names, hashes and examples.
- Reproduction from release assets: ensure scripts identify the downloadable DB and outputs without relying on ignored local files.
- Git cleanliness: stage only release deliverables and preserve the user's existing modifications/untracked work.
- Data redistribution: retain previously released text coverage and source attribution/terms; do not accidentally include unrelated raw caches.

---

### Task 1: Define the canonical data export and manifest

**Files:**
- Modify: `50_generate_final_tables.py`
- Modify: `data/release_v4/README.md`
- Modify: `docs/RELEASE_MANIFEST_V4_20260908.json`

**Interfaces:**
- Produces: canonical score export and manifest with row counts, cohorts, source DB/table, model/prompt/segmentation, hashes and validation links.

- [ ] Select documented GPT-5.6 v4 scores and record full-run versus pilot provenance explicitly; keep pilot distinct if protocol metadata differs.
- [ ] Make the release tables reproducible from the full analytical DB, not the website-only DB.
- [ ] Rebuild compact CSV/Parquet and manifest metadata from the selected snapshot.

### Task 2: Correct reproduction and repository documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/REPRODUCIBILITY.md`
- Modify: `docs/DATA_DICTIONARY.md`
- Modify: `docs/CODE_MAP.md`
- Modify: `CITATION.cff`

- [ ] Explain v4.0 Qwen/chunked versus v4.1.0 GPT-5.6/full-text, and identify which reproduces the submitted article.
- [ ] Document full DB and website DB roles, release download path, schema, commands, environment and source manifests.
- [ ] State precise cohort composition, six dimensions, filters and limitations; resolve inconsistent counts across docs.

### Task 3: Assemble and publish the v4.1.0 asset

**Files:**
- Create or regenerate: `data/release_v4/analysis/*` and validation metadata as needed
- GitHub release: `v4.1.0` notes and assets

- [ ] Prepare a public DuckDB asset with the required texts, scores and provenance, without unrelated working files or secrets.
- [ ] Compute asset and export SHA-256; add download instructions and hashes to the manifest/release notes.
- [ ] Update the existing GitHub v4.1.0 release with database and portable exports, preserving the tag and release history.

### Task 4: Hand off a reproducible package

- [ ] Review only intended Git changes and avoid staging the user's unrelated existing work.
- [ ] Confirm release notes, filenames, hashes and local instructions point to the same v4.1.0 snapshot.

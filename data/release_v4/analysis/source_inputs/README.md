# Validation source inputs

These files are the small, frozen crosswalk and prompt-sensitivity inputs used by `tools/reproduce_validation_audit.py`. They let an external analyst regenerate the packaged validation tables with the release DuckDB, without relying on a user's private working paths or temporary backup files.

## Files

- `gpd_popin_leader_term_matches.csv` — curated leader–mandate crosswalk used for GPD validation.
- `gpd_popin_match_review.csv` — reviewed discourse-level match candidates and decisions.
- `sensitivity_test_sample.csv` — frozen 900-document prompt-sensitivity sample.
- `sensitivity_runs/*.jsonl` and matching metadata — stored model outputs used to audit prompt sensitivity and raw response integrity.

The Global Populism Database v2.1 is available from Harvard Dataverse under DOI [10.7910/DVN/LFTQEZ](https://doi.org/10.7910/DVN/LFTQEZ); Harvard Dataverse lists the dataset under CC0 1.0. The source observations used for the released analysis are also retained in the DuckDB `raw_gpd_long` and `raw_gpd_wide` tables. The GPD codebook and exact source version are described in `GPD_V2_1_20251120_MANIFEST.md`.

LALLPI v2025.1 is cited by DOI [10.7910/DVN/KEJ9VF](https://doi.org/10.7910/DVN/KEJ9VF); its data page provides the version-specific download and codebook. The table used in the validation is retained in DuckDB as `raw_lallpi_index`. See `LALLPI_V2025_MANIFEST.md` for source and version details.

The crosswalks contain researcher decisions and are not the raw GPD data. Preserve them unchanged when regenerating results. For a new match review, create a new versioned file and record the adjudication rules.

# Conventions — Coding Patterns

> **Evidence:** INFERRED from `origin/Public` (read-only). No code on `main`.
> Pattern strength labels per spec.

## Feature placement (INFERRED, weak — ~1 repo, no framework)
- New analysis scripts: top-level `.py` files, standalone, run directly.
- New shell collection scripts: top-level `.sh` or under a topic dir (`CreateSecurityPatch/`, `StatsCollector/`, `AccessValidate/`).
- Notebooks: top-level `.ipynb`.
- Data dictionaries: `Dictionaries/`.
- No package structure, no `src/` layout. **unknown** whether a convention is intended.

## Naming and structure (INFERRED, weak)
- Files: `PascalCase` for scripts (`FileUsageReport.sh`, `PackageUsageReport.py`); `snake_case` for utility modules (`access_times.py`, `buffer_unitizer.py`).
- Functions: `snake_case` (`read_csv_filter_convert`, `print_intervals`).
- No class hierarchy observed; scripts are procedural.
- Count: ~2 snake_case modules, ~6 PascalCase scripts on origin/Public.

## Error handling (INFERRED, weak)
- No custom error classes. Errors surface as pandas exceptions or `print` messages + `exit 1` in Bash.
- Bash scripts use `|| { echo '...'; exit 1; }` in one place (SSH failure).
- No structured logging; `print()` only. **unknown** for retryable/non-retryable distinction.

## Validation (INFERRED, weak)
- `ModifiedPackageUsageReportWithValidation.py` is the only script with input validation: `read_validate_csv` enforces column count + numeric coercion, with a 5% error threshold per file.
- Other scripts use `access_times.read_csv_filter_convert` which silently drops malformed rows and counts non-convertibles.
- No validation library (e.g. pydantic, marshmallow). Count: 1 validating script.

## Testing conventions (UNKNOWN)
- No tests observed on `main` or inferred on `origin/Public` (no `test_*.py`, `*_test.py`, or test dirs in the file listing). **unknown**.

## Strength summary
| Convention | Strength |
|-----------|----------|
| Standalone top-level scripts | weak (~8 occurrences, INFERRED) |
| snake_case Python functions | weak (~4 occurrences, INFERRED) |
| PascalCase script filenames | weak (~6 occurrences, INFERRED) |
| print-based output | weak (~all scripts, INFERRED) |
| Hardcoded input paths | weak (~2 occurrences, INFERRED) |
| CSV/PSV delimited data | weak (~4 files, INFERRED) |
| Formal layering / packaging | unknown |
| Testing | unknown |

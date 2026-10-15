# Components — Index

> All components below are **DECLARED** in `README.md` / **INFERRED** from
> `origin/Public` (read-only). None are **OBSERVED** on `main` — no source
> files exist on `main`. Verify against `origin/Public` before editing.

| Component | Responsibility | File |
|-----------|---------------|------|
| File usage analysis | Collect filesystem `atime` to find never-accessed files | [file-usage-analysis.md](file-usage-analysis.md) |
| Package usage analysis | Cross-reference packages with file access data | [package-usage-analysis.md](package-usage-analysis.md) |
| Security patch pipeline | Build & install patches stripping unused components | [security-patch-pipeline.md](security-patch-pipeline.md) |
| Stats collector | Longitudinal VM file-usage stats collection | [stats-collector.md](stats-collector.md) |

For machine-readable dependency/impact data, see
[../change-impact/relationships.yaml](../change-impact/relationships.yaml).

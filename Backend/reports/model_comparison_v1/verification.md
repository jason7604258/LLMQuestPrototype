# Verification — 2026-09-09

The offline four-model analysis completed successfully.

- Full backend suite: **74 tests passed**, including 22 new cohort/comparison tests. The API key was cleared; model clients were mocked in backend tests. Local loopback HTTP tests required running outside the filesystem/network sandbox.
- Four cohorts: 288 generations total, 1,160 unordered within-scenario narrative pairs, 2,320 field rows, and 160 audit pairs (40 per model).
- Three new MPNet analyses: CPU/float32, pinned revision and package versions matching Sol, offline model loading, zero truncated texts. No narrative API calls or model downloads.
- Re-executed the entire three-model lexical/semantic pipeline and the four-model comparator. All **52 analysis/input/manifest/report files** had identical SHA-256 values before and after the rerun.
- Separately checked **20 existing source/Sol files** against hashes captured before this work: all unchanged. This includes all five raw JSONL logs, all existing Sol lexical/semantic reports, and the existing Sol combined Markdown report.
- Independent CSV QA using the bundled spreadsheet runtime: 8 macro rows and 64 scenario rows; **64 macro/pooled aggregation checks** passed. Another **16 primary-metric checks** matched calculations performed independently before report generation. Tolerance accounts for nine-decimal summary serialization.
- Imported the summary CSV through ArtifactTool, checked numeric conversion, inspected the table, and rendered/viewed a temporary preview. No Excel workbook was introduced or original CSV rewritten by this QA.

Read [model_comparison.md](model_comparison.md) for results and limitations. This verification establishes data/implementation consistency, not independent human validation of narrative meaning or quality.

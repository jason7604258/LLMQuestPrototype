# Step 18 — Offline Experiment Analysis

## Goal

Convert the append-only Step 17 JSONL log into dissertation-ready summary
statistics and inspect narrative repetition with the `lexical-field-v2`
method. The analyzer is completely offline: it does not call OpenAI, consume
tokens, or add API cost.

## Run

From the project root:

```bash
Backend/.venv/bin/python Backend/analyze_experiments.py
```

The backend server may remain running. Restarting it is not necessary because
the analyzer only reads the log file.

## Outputs

The command writes six files to `Backend/reports/`:

- `experiment_summary.md`: readable overview of reliability, latency, cost,
  gameplay completion, repetition, and per-scenario results.
- `generation_records.csv`: one analysis row per generated narrative, joined
  to its start/completion events when available.
- `scenario_summary.csv`: aggregate results for every fixed scenario.
- `lexical_field_summary.csv`: field-level lexical statistics, pair counts,
  and review/high-similarity rates for the primary within-scenario analysis
  and secondary cross-scenario analysis.
- `similar_narratives.csv`: every field-level pair for `introduction` and
  `completionText`, including its scope, similarity score, and threshold band.
- `repeated_titles.csv`: exact repeated titles after normalization, with their
  scenario and request IDs.

The analyzer reads both legacy schema-version-1 generation records and current
schema-version-2 generation/lifecycle records. Old records have no gameplay
events, so they contribute to generation, cost, latency, and repetition
statistics but not to the gameplay completion rate.

## Lexical-field-v2 repetition metric

The analyzer normalizes text with Unicode NFKC normalization, case folding,
punctuation removal, and whitespace collapsing. It then compares
`introduction` and `completionText` separately instead of combining several
narrative fields into one score. This makes repetition in one field visible
even when the other field uses different wording.

Each field score is the average of forward and reverse Python
`SequenceMatcher` character-sequence ratios with `autojunk=False`. Averaging
both directions prevents log order from changing the result, while disabling
autojunk avoids discarding frequent characters in longer introductions.

Pairs from the same fixed scenario are the primary analysis because they share
the same gameplay facts. Pairs from different scenarios are reported as a
secondary analysis for detecting wording templates that recur across the
whole scenario pool. Reports include the number of eligible pairs so rates
from scenarios with different generation counts can be interpreted fairly.

Field-level similarities use two fixed reporting bands:

- Review similarity: at least 80% and below 85%.
- High similarity: at least 85%.

Titles are not assigned a fuzzy similarity score. A title is counted as a
repeat only when it is exactly equal after the same NFKC, case-folding,
punctuation, and whitespace normalization. The fixed `objectiveText`, target
display names, and rolling `storySummary` are outside this lexical-field
metric.

This method detects repeated wording. It is not a semantic similarity score
and does not replace human evaluation of coherence, creativity, or story
quality.

To change the two inclusive thresholds while preserving the review-before-high
ordering:

```bash
Backend/.venv/bin/python Backend/analyze_experiments.py \
  --review-threshold 0.80 \
  --similarity-threshold 0.85
```

## Custom input and output

```bash
Backend/.venv/bin/python Backend/analyze_experiments.py \
  --input Backend/logs/narrative_runs.jsonl \
  --output-dir Backend/reports
```

Running the analyzer again safely overwrites only the generated report files;
it never modifies the source JSONL log.

## Frozen 72 word-level follow-up

The demo log is append-only and now contains records added after the original
72-generation experiment. The reproducible word-level analysis therefore reads
only its first 206 physical lines, which contain 72 generation records and 134
gameplay events:

```bash
Backend/.venv/bin/python Backend/analyze_lexical_similarity.py
```

The command writes a separate report set to
`Backend/reports/lexical_frozen72_v3/` and records a SHA-256 digest of the exact
input prefix. The default run fails closed unless that digest matches the known
frozen prefix. It analyzes all unordered pairs sharing the same exact
`scenarioId`, with `introduction` and `completionText` kept separate. Token LCS
F1 is the primary ordered-overlap metric, calculated as
`2 × LCS length / (tokens A + tokens B)`; the subsequence preserves relative
order but may contain gaps. Word 3-gram Jaccard compares sets of unique
contiguous three-word sequences, while word 1-gram Jaccard compares sets of
unique words. Jaccard therefore ignores frequency, and the 1-gram form also
ignores order. No high/review cutoff is assigned because the earlier
SequenceMatcher thresholds are not transferable to these word-level scores.

The output includes all 592 field rows, overall and per-scenario summaries,
top-pair tables, and a 40-pair qualitative audit sample. The audit sample is
allocated proportionally across scenarios and selected by deterministic
SHA-256 ranking with the experiment-date salt `20260820`. It is an inspection
sample rather than human validation; all 296 narrative pairs contribute to the
numerical summaries. Overall values are pooled pair-weighted descriptive
statistics; per-scenario rows are also reported because scenario pair counts
range from 21 to 55 and pair observations are not independent.

## Frozen 72 semantic follow-up

The semantic analysis reuses the exact frozen input prefix, persisted 592
lexical field rows, and existing 40-pair audit sample. Install the pinned
runtime once:

```bash
Backend/.venv/bin/python -m pip install -r Backend/requirements-semantic.txt
```

The default command deliberately loads the model from the local cache only:

```bash
Backend/.venv/bin/python Backend/analyze_semantic_similarity.py
```

On a new machine, permit one download of the pinned model revision first:

```bash
Backend/.venv/bin/python Backend/analyze_semantic_similarity.py --allow-download
```

The analyzer locks `sentence-transformers/all-mpnet-base-v2` to revision
`e8c3b32edf5434bc2275fc9bab85f82640a19130`, CPU, and float32 output. It
collapses whitespace but otherwise preserves case, punctuation, stopwords, and
word forms. Each of the 144 unique `(scenarioId, field, requestId)` texts is
embedded once as a normalized 768-dimensional vector. Cosine is the dot
product between two normalized vectors. It ranges from -1 to 1, but is neither
a probability nor a percentage.

Only the same 296 unordered within-scenario pairs are compared, with
`introduction` and `completionText` kept separate. The strict join key is
`(comparisonScope, scenarioId, field, requestIdA, requestIdB)`. The command
stops if the frozen input, lexical/audit hashes, row order, source text, or
recomputed lexical metrics differ. The current data use at most 59 of the
model's 384-wordpiece limit, so no analyzed text is truncated.

Outputs are written to `Backend/reports/semantic_frozen72_v1/`:

- `semantic_analysis_summary.md`: method, overall/per-scenario statistics,
  correlations, top pairs, and interpretation limits.
- `analysis_metadata.json`: input, analyzer, lexical report, model snapshot,
  package-version, preprocessing, and truncation provenance.
- `within_scenario_semantic_pairs.csv`: all 592 field rows, with semantic cosine
  and all three lexical measurements beside it.
- `within_scenario_semantic_summary.csv`: pair-weighted overall and per-scenario
  mean, median, P90, minimum, and maximum, plus an equal-scenario macro mean.
- `lexical_semantic_correlations.csv`: Spearman rho (primary) and Pearson r
  (supplementary) between semantic cosine and each lexical measurement.
- `top_semantic_pairs.csv`: ten highest semantic-cosine pairs per field with
  source text and lexical scores.
- `hash_ranked_audit_sample_40_with_semantic.csv`: the same 40 lexical audit
  pairs, in the same order, enriched with both semantic field scores.
- `embedded_text_manifest.csv`: text hashes, token lengths, truncation flags,
  and embedding-norm checks for all 144 embedded identities.

No semantic high/review cutoff is assigned without human calibration. High
within-scenario similarity can result from required shared scenario facts as
well as repetitive writing. Semantic cosine therefore stays separate beside
Token LCS F1 and Word 3-gram Jaccard; the scores are not averaged into one
quality number. Spearman is the primary lexical–semantic association because
the relationship need not be linear and lexical scores contain ties. These
pooled correlations may also include scenario-level differences. P-values are
omitted because the pair rows repeatedly reuse narratives and are not
independent.

## Combined frozen-72 findings

After the frozen lexical and semantic analyzers have both completed, generate
the integrated Results-oriented report with:

```bash
Backend/.venv/bin/python Backend/analyze_combined_findings.py
```

The command writes
`Backend/reports/combined_frozen72_v1/combined_findings.md`. It verifies that
the experiment, lexical, semantic, and 40-pair audit files still refer to the
same frozen requests before joining them. It presents overall and scenario
profiles, lexical–semantic correlations, and examples with the largest
semantic-versus-LCS average-rank percentile gaps. Those gaps select cases for
inspection only; they do not create high/low quality labels. The formal source
CSV files are read without modification, preserving raw and derived data
separation.

## Four-model gameplay comparison

The follow-up compares the existing Sol cohort with Terra, Luna, and Astra.
The lexical and semantic metric implementations are unchanged. Prepare the
cohorts and run the three new analyses entirely offline with:

```bash
Backend/.venv/bin/python Backend/run_model_analysis.py
Backend/.venv/bin/python Backend/analyze_model_comparison.py \
  --manifest Backend/reports/model_comparison_v1/analysis_manifest.json \
  --output-dir Backend/reports/model_comparison_v1
```

Use `--prepare-only` on the first command to inspect cohort provenance before
running the analysis. Source JSONL files and the existing Sol reports are not
overwritten. New outputs reside under `Backend/reports/model_comparison_v1/`.

### Fixed analysis cohorts

| Model requested | Source JSONL | Source physical-line prefix | Selected generations | Selection |
|---|---|---:|---:|---|
| `gpt-5.6-sol` | `demo_narrative_runs_2026-08-20_take01.jsonl` | 206 | 72 | Preserve the original frozen cohort and reports. |
| `gpt-5.6-terra` | `terra_gameplay_run01.jsonl` | 216 | 72 | Preserve the first 72 complete generation/start/completion records. |
| `gpt-5.6-luna` | `luna_gameplay_run01.jsonl` | 217 | 72 | Exclude only the known connection-error fallback at physical line 1; preserve the following 72 OpenAI generations and their events. |
| `gpt-6-astra` | `astra_gameplay_run01.jsonl` | 216 | 72 | Preserve the first 72 complete generation/start/completion records. |

These boundaries follow the planned 72-generation collection, not similarity
scores. The extra automatically started quest after each completed new run is
outside its cohort. Excluded records remain in the original logs. Luna's
connection failure is retained in provenance and must still count in any
separate API-reliability analysis; its fixed fallback text is not a Luna
generated narrative.

The preparation manifest records original-prefix and derived-input hashes,
request IDs, and source-line mappings. Derived inputs retain the selected raw
JSONL bytes. Acceptance flags are checked after selecting the fixed cohort,
not used to silently discard additional records. Unexpected models, failures,
counts, or changed source prefixes stop the workflow.

Sol has 8/9/10/10/10/7/11/7 generations in scenario-ID order, yielding 296
unordered within-scenario narrative pairs. Each new cohort has 9 generations
for each of 8 scenarios, yielding 288 pairs. With two separately analyzed
fields, these are 592 and 576 field comparisons respectively.

### Comparison and interpretation

For each model, field, and metric, compute every scenario's within-scenario
pair mean first. The primary overall summary is the arithmetic mean of the
eight scenario means: every scenario contributes one eighth. Pooled
pair-weighted means remain secondary descriptions, because Sol's unequal
scenario sizes would otherwise give different scenario weights. Metrics and
fields are never averaged together into a single quality score.

The cross-model report derives statistics from the persisted six-decimal pair
CSV values. It validates input identities, pair coverage, and shared analysis
settings before comparing models. The fixed MPNet revision, model-file
fingerprint, CPU/float32 configuration, preprocessing, and package versions
must match the existing Sol semantic analysis. Model downloads and narrative
API requests are not part of this offline workflow.

Each new model also receives a deterministic 40-pair audit using the existing
proportional SHA-256-ranked selection method and salt `20260820`. Semantic
analysis enriches that model's same audit pairs; the four models do not share
identical request IDs or identical selected text pairs. Neither these samples
nor metric-disagreement cases constitute human validation.

Read `model_comparison.md` first, then `scenario_comparison.csv` and
`model_macro_summary.csv` for detailed results. The per-model `lexical/` and
`semantic/` folders preserve full pairs, summaries, audit samples, and metadata.

The completed 2026-09-09 run is documented in
`Backend/reports/model_comparison_v1/verification.md`: 74 backend tests passed,
all 52 derived analysis files were byte-identical on a full rerun, and the
pre-existing raw logs and Sol artifacts checked before/after were unchanged.
The CSV macro and pooled summaries also passed independent aggregation checks.

These results describe the collected gameplay outputs. Shared texts make pair
rows statistically dependent; 296 or 288 pairs are not that many independent
experimental observations. Scenario order and rolling `previousStorySummary`
inputs differ across runs, and equal-scenario averaging does not eliminate
that difference. Similarity is not narrative quality or creativity, and this
design does not establish a causal model advantage. Recorded generation model
names are the API request model names; the original logs do not separately
retain the API-returned model identifier.

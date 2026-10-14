# Reading and rerunning the analysis code

## Why some source files retain their existing comments

Three analysis modules are checked against hashes recorded with the original
results: `analyze_experiments.py`, `analyze_lexical_similarity.py` and
`analyze_semantic_similarity.py`. They already contain function documentation.
Their bytes have been preserved because changing even a comment would fail
the historical source checks. This guide adds reading notes without changing
those original files.

The combined report, dataset runner and four-model comparator received extra
comments for submission. Their original versions are retained in
`Backend/historical_analysis_sources/`; the current versions have the same
Python abstract syntax trees. Existing docstrings and executable statements
were retained. Plain comments explain the steps and limitations.

## Code map

| Module | Purpose and boundary |
| --- | --- |
| `analyze_experiments.py` | Reads generation and lifecycle records and supplies shared record/text helpers. Its earlier character comparison is separate from the dissertation's later word and embedding comparison. |
| `analyze_lexical_similarity.py` | Verifies the selected source prefix, normalises text, forms pairs within a scenario, calculates Token LCS F1 and word Jaccard scores, and writes a reproducible inspection sample. It does not judge narrative quality. |
| `analyze_semantic_similarity.py` | Checks lexical pair identities against the source text, encodes the two fields separately, calculates cosine similarity and links semantic scores to lexical pairs. Record-to-vector alignment is checked before writing results. |
| `analyze_combined_findings.py` | Combines the original Sol reports, correlates lexical and semantic scores and identifies examples of disagreement. |
| `run_model_analysis.py` | Selects the fixed source ranges for the four models, checks scenario facts and generation/lifecycle records, and invokes the original analysers under strict environment checks. |
| `analyze_model_comparison.py` | Verifies persisted pairs and settings, calculates scenario and overall means, and writes correlations and diagnostic cases. |
| `Tools/reproduce_saved_comparison.py` | Checks the submitted evidence and reruns the saved-score comparison in a relocated project. It does not load MPNet or request new narratives. |

The main mean gives every scenario equal weight. The secondary pooled mean
gives every pair equal weight. These differ for Sol because its scenario counts
differ. A narrative can appear in several pairs, so the number of pairs is not
a count of independent observations. Neither lexical nor semantic similarity
is a validated measure of enjoyment or narrative quality.

## Fresh lexical and semantic runs for the later datasets

Run commands from the extracted project root. Install the backend and semantic
requirements as described in the main README. Use a fresh output directory for
each dataset. The selected inputs already exclude the first Luna fallback;
the full Luna source log still includes it.

| Dataset | Selected input | Lines | SHA-256 of these input bytes |
| --- | --- | ---: | --- |
| Terra | `Backend/reports/model_comparison_v1/terra/input_frozen72.jsonl` | 216 | `2db1a0430dc58316d6419db420980d4c48468fad8b003b799ae36b30f1c13b1b` |
| Luna | `Backend/reports/model_comparison_v1/luna/input_frozen72.jsonl` | 216 | `5f05b7b1e96ab17de58b89cd9bcad3f23f62eba9b8a1571dcd60d2b79940c568` |
| Astra | `Backend/reports/model_comparison_v1/astra/input_frozen72.jsonl` | 216 | `0c8529814f8adfae0100bc769964939be1cb8882f5376ce9ae05edae78f6a440` |

For example, Terra can be recalculated with:

```bash
python Backend/analyze_lexical_similarity.py \
  --input Backend/reports/model_comparison_v1/terra/input_frozen72.jsonl \
  --max-lines 216 \
  --expected-prefix-sha256 2db1a0430dc58316d6419db420980d4c48468fad8b003b799ae36b30f1c13b1b \
  --output-dir Reanalysis/terra/lexical

python Backend/analyze_semantic_similarity.py \
  --input Backend/reports/model_comparison_v1/terra/input_frozen72.jsonl \
  --max-lines 216 \
  --expected-prefix-sha256 2db1a0430dc58316d6419db420980d4c48468fad8b003b799ae36b30f1c13b1b \
  --output-dir Reanalysis/terra/semantic \
  --lexical-pairs Reanalysis/terra/lexical/within_scenario_lexical_pairs.csv \
  --lexical-audit Reanalysis/terra/lexical/hash_ranked_audit_sample_40.csv \
  --allow-download
```

For Luna or Astra, replace the dataset name in all paths and use its hash from
the table. Omit `--allow-download` once the exact model revision is cached.
Do not compare a semantic report with lexical files from another dataset.

These commands recalculate individual datasets. They do not claim that a new
machine reproduces the historical files byte for byte: report paths and
environment metadata will reflect the new run. The original runner's strict
environment checks remain unchanged. The portable helper checks and
recalculates the supplied scores separately, without relaxing the original
algorithms or presenting new model output as historical data.

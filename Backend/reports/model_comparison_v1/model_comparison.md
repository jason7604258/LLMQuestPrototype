# Four-model lexical and semantic comparison

Descriptive analysis of 72 generated narratives per model. Higher scores mean more similarity/overlap, not better or worse writing.

## Main results: equal-scenario means

Each scenario contributes 1/8. Introduction and completionText are separate; metrics are never averaged together.

| Model | Field | Token LCS F1 | Word 3-gram Jaccard | Word 1-gram Jaccard | MPNet cosine |
|---|---|---:|---:|---:|---:|
| Sol | introduction | 0.3200 | 0.0470 | 0.2694 | 0.8020 |
| Sol | completionText | 0.3582 | 0.0362 | 0.2221 | 0.6527 |
| Terra | introduction | 0.2962 | 0.0316 | 0.2383 | 0.7371 |
| Terra | completionText | 0.3521 | 0.0338 | 0.2206 | 0.6544 |
| Luna | introduction | 0.3264 | 0.0514 | 0.2664 | 0.7476 |
| Luna | completionText | 0.3558 | 0.0411 | 0.2263 | 0.7300 |
| Astra | introduction | 0.3784 | 0.0727 | 0.3171 | 0.8120 |
| Astra | completionText | 0.3582 | 0.0579 | 0.2727 | 0.7477 |

Key observations in this dataset:

- Astra has the highest introduction macro means on all four metrics. This describes stronger within-scenario overlap, not a quality ranking.
- Completion LCS means are close (0.3521–0.3582), whereas semantic means differ more: Sol 0.6527, Terra 0.6544, Luna 0.7300, Astra 0.7477.
- Similar lexical averages do not imply similar semantic averages. Read the original passages before attributing a pattern to templates, paraphrases, or required facts.

## Introduction versus completion across the eight scenarios

| Model | Introduction cosine > completion | Completion LCS > introduction |
|---|---:|---:|
| Sol | 8/8 | 7/8 |
| Terra | 8/8 | 8/8 |
| Luna | 5/8 | 6/8 |
| Astra | 6/8 | 3/8 |

## Lexical–semantic rank relationships

Spearman uses average ranks for ties. Pair-level compares pairs within a model/field; scenario-level compares just eight scenario means. These are distinct levels, not interchangeable evidence.

| Model | Field | Pair semantic–LCS Spearman | Scenario-mean semantic–LCS Spearman |
|---|---|---:|---:|
| Sol | introduction | 0.4556 | 0.6429 |
| Sol | completionText | 0.6035 | -0.0714 |
| Terra | introduction | 0.5796 | 0.6429 |
| Terra | completionText | 0.5974 | 0.8571 |
| Luna | introduction | 0.5694 | 0.1667 |
| Luna | completionText | 0.6335 | 0.7857 |
| Astra | introduction | 0.4417 | 0.3571 |
| Astra | completionText | 0.6748 | 0.8810 |

## Scenario detail

Every cell is a within-scenario mean; there are no cross-model text-pair scores in these tables.

### introduction

| Scenario | Model | Generations | Pairs | LCS | Word 3-gram | Cosine |
|---|---|---:|---:|---:|---:|---:|
| collect_mushroom_01 | Sol | 8 | 28 | 0.3074 | 0.0249 | 0.8059 |
| collect_mushroom_01 | Terra | 9 | 36 | 0.3194 | 0.0274 | 0.7724 |
| collect_mushroom_01 | Luna | 9 | 36 | 0.3296 | 0.0417 | 0.7777 |
| collect_mushroom_01 | Astra | 9 | 36 | 0.4012 | 0.1012 | 0.7951 |
| kill_torch_01 | Sol | 9 | 36 | 0.3160 | 0.0359 | 0.8060 |
| kill_torch_01 | Terra | 9 | 36 | 0.3272 | 0.0388 | 0.7631 |
| kill_torch_01 | Luna | 9 | 36 | 0.3285 | 0.0373 | 0.7931 |
| kill_torch_01 | Astra | 9 | 36 | 0.2795 | 0.0430 | 0.7975 |
| slay_caveborn_bear_01 | Sol | 10 | 45 | 0.3235 | 0.0545 | 0.8340 |
| slay_caveborn_bear_01 | Terra | 9 | 36 | 0.2821 | 0.0335 | 0.7177 |
| slay_caveborn_bear_01 | Luna | 9 | 36 | 0.3289 | 0.0754 | 0.7238 |
| slay_caveborn_bear_01 | Astra | 9 | 36 | 0.3840 | 0.0762 | 0.8329 |
| slay_caveborn_lizard_01 | Sol | 10 | 45 | 0.3299 | 0.0564 | 0.7937 |
| slay_caveborn_lizard_01 | Terra | 9 | 36 | 0.2666 | 0.0237 | 0.6875 |
| slay_caveborn_lizard_01 | Luna | 9 | 36 | 0.3228 | 0.0546 | 0.7021 |
| slay_caveborn_lizard_01 | Astra | 9 | 36 | 0.4845 | 0.1181 | 0.8286 |
| slay_caveborn_snake_01 | Sol | 10 | 45 | 0.3003 | 0.0482 | 0.8085 |
| slay_caveborn_snake_01 | Terra | 9 | 36 | 0.2815 | 0.0362 | 0.7738 |
| slay_caveborn_snake_01 | Luna | 9 | 36 | 0.3355 | 0.0644 | 0.7546 |
| slay_caveborn_snake_01 | Astra | 9 | 36 | 0.3667 | 0.0549 | 0.8005 |
| slay_caveborn_spider_01 | Sol | 7 | 21 | 0.3663 | 0.0886 | 0.8505 |
| slay_caveborn_spider_01 | Terra | 9 | 36 | 0.2776 | 0.0246 | 0.6615 |
| slay_caveborn_spider_01 | Luna | 9 | 36 | 0.3406 | 0.0537 | 0.7391 |
| slay_caveborn_spider_01 | Astra | 9 | 36 | 0.3692 | 0.0569 | 0.8286 |
| slay_caveborn_turtle_01 | Sol | 11 | 55 | 0.3444 | 0.0516 | 0.8116 |
| slay_caveborn_turtle_01 | Terra | 9 | 36 | 0.2881 | 0.0408 | 0.7299 |
| slay_caveborn_turtle_01 | Luna | 9 | 36 | 0.3037 | 0.0507 | 0.7288 |
| slay_caveborn_turtle_01 | Astra | 9 | 36 | 0.3972 | 0.0800 | 0.8323 |
| slay_torch_boss_01 | Sol | 7 | 21 | 0.2720 | 0.0156 | 0.7059 |
| slay_torch_boss_01 | Terra | 9 | 36 | 0.3271 | 0.0278 | 0.7908 |
| slay_torch_boss_01 | Luna | 9 | 36 | 0.3215 | 0.0339 | 0.7614 |
| slay_torch_boss_01 | Astra | 9 | 36 | 0.3450 | 0.0517 | 0.7802 |

### completionText

| Scenario | Model | Generations | Pairs | LCS | Word 3-gram | Cosine |
|---|---|---:|---:|---:|---:|---:|
| collect_mushroom_01 | Sol | 8 | 28 | 0.3278 | 0.0389 | 0.6448 |
| collect_mushroom_01 | Terra | 9 | 36 | 0.3357 | 0.0191 | 0.6630 |
| collect_mushroom_01 | Luna | 9 | 36 | 0.2759 | 0.0322 | 0.6444 |
| collect_mushroom_01 | Astra | 9 | 36 | 0.2998 | 0.0356 | 0.6763 |
| kill_torch_01 | Sol | 9 | 36 | 0.2764 | 0.0099 | 0.6463 |
| kill_torch_01 | Terra | 9 | 36 | 0.4348 | 0.0715 | 0.7586 |
| kill_torch_01 | Luna | 9 | 36 | 0.3696 | 0.0421 | 0.7759 |
| kill_torch_01 | Astra | 9 | 36 | 0.2353 | 0.0127 | 0.6071 |
| slay_caveborn_bear_01 | Sol | 10 | 45 | 0.4229 | 0.0591 | 0.7045 |
| slay_caveborn_bear_01 | Terra | 9 | 36 | 0.3971 | 0.0433 | 0.6739 |
| slay_caveborn_bear_01 | Luna | 9 | 36 | 0.3943 | 0.0427 | 0.7843 |
| slay_caveborn_bear_01 | Astra | 9 | 36 | 0.4668 | 0.1144 | 0.8399 |
| slay_caveborn_lizard_01 | Sol | 10 | 45 | 0.3733 | 0.0471 | 0.6283 |
| slay_caveborn_lizard_01 | Terra | 9 | 36 | 0.3069 | 0.0271 | 0.5413 |
| slay_caveborn_lizard_01 | Luna | 9 | 36 | 0.3792 | 0.0461 | 0.7363 |
| slay_caveborn_lizard_01 | Astra | 9 | 36 | 0.3284 | 0.0410 | 0.6978 |
| slay_caveborn_snake_01 | Sol | 10 | 45 | 0.3424 | 0.0316 | 0.6404 |
| slay_caveborn_snake_01 | Terra | 9 | 36 | 0.3170 | 0.0282 | 0.6026 |
| slay_caveborn_snake_01 | Luna | 9 | 36 | 0.2818 | 0.0270 | 0.6605 |
| slay_caveborn_snake_01 | Astra | 9 | 36 | 0.4502 | 0.0935 | 0.8445 |
| slay_caveborn_spider_01 | Sol | 7 | 21 | 0.4109 | 0.0427 | 0.6026 |
| slay_caveborn_spider_01 | Terra | 9 | 36 | 0.3201 | 0.0254 | 0.6220 |
| slay_caveborn_spider_01 | Luna | 9 | 36 | 0.3651 | 0.0396 | 0.7325 |
| slay_caveborn_spider_01 | Astra | 9 | 36 | 0.3656 | 0.0562 | 0.8086 |
| slay_caveborn_turtle_01 | Sol | 11 | 55 | 0.3720 | 0.0395 | 0.6529 |
| slay_caveborn_turtle_01 | Terra | 9 | 36 | 0.2988 | 0.0196 | 0.6235 |
| slay_caveborn_turtle_01 | Luna | 9 | 36 | 0.3577 | 0.0352 | 0.7483 |
| slay_caveborn_turtle_01 | Astra | 9 | 36 | 0.4213 | 0.0816 | 0.7777 |
| slay_torch_boss_01 | Sol | 7 | 21 | 0.3396 | 0.0210 | 0.7016 |
| slay_torch_boss_01 | Terra | 9 | 36 | 0.4062 | 0.0364 | 0.7505 |
| slay_torch_boss_01 | Luna | 9 | 36 | 0.4224 | 0.0638 | 0.7575 |
| slay_torch_boss_01 | Astra | 9 | 36 | 0.2981 | 0.0285 | 0.7301 |

## Cohorts and validation

| Model | Generations | Narrative pairs | Field rows | Audit pairs | Max wordpieces | Truncated texts |
|---|---:|---:|---:|---:|---:|---:|
| Sol | 72 | 296 | 592 | 40 | 59 | 0 |
| Terra | 72 | 288 | 576 | 40 | 55 | 0 |
| Luna | 72 | 288 | 576 | 40 | 51 | 0 |
| Astra | 72 | 288 | 576 | 40 | 65 | 0 |

- Sol keeps its original frozen first 206 physical lines and existing reports: unequal scenario counts, 72 starts, 62 logged completions. It is not relabeled as a 72-completion cohort.
- Terra/Astra use the first 216 physical lines. Luna uses the first 217 excluding only its known line-1 connection-error fallback. The extra automatically started quest is outside each fixed new cohort; nothing is deleted from raw logs.
- Each new cohort has nine generations per scenario, 72 starts/completions, empty initial continuity, and later summaries matching the preceding generation. Event POST arrival order can differ from generation order (Luna); coverage and summary chains are checked separately.
- Source prefix hashes, derived bytes, exact pair keys/texts/lexical scores, audit identities, and shared analyzer/model/runtime settings are verified before aggregation.
- MPNet: sentence-transformers/all-mpnet-base-v2; revision e8c3b32edf5434bc2275fc9bab85f82640a19130; 768 dimensions; CPU/float32; 384 wordpiece limit; offline load. No narrative API calls are made.
- Lexical uses NFKC/casefold/punctuation-to-space word tokenization. Semantic only collapses whitespace. Model settings match the original Sol analysis.
- Statistics here are calculated from persisted six-decimal pair CSV values; derived CSV summaries use nine decimals. Tiny last-digit correlation differences from per-model reports can arise because those reports use pre-serialization cosine values.

## Which files to read

- [Scenario detail](scenario_comparison.csv): 64 model/scenario/field rows, all four metrics.
- [Macro and secondary pooled means](model_macro_summary.csv): eight model/field rows. Pooled means are not the primary cross-model comparison.
- [Correlations](pair_correlations.csv): semantic versus each lexical metric at pair and scenario-mean levels.
- [Metric disagreement cases](metric_disagreement_cases.csv): five largest absolute semantic–LCS rank-percentile gaps per model/field, with original texts. Percentile = (N − descending average rank)/(N − 1). No quality cutoff or paraphrase label is assigned.
- [Cohort provenance](analysis_manifest.json) and [verification metadata](comparison_metadata.json).

Per-model reports and fixed audit samples:

- Sol: [lexical report](<PROJECT_ROOT>/Backend/reports/lexical_frozen72_v3/lexical_analysis_summary.md), [semantic report](<PROJECT_ROOT>/Backend/reports/semantic_frozen72_v1/semantic_analysis_summary.md), [40-pair audit with texts and semantic scores](<PROJECT_ROOT>/Backend/reports/semantic_frozen72_v1/hash_ranked_audit_sample_40_with_semantic.csv).
- Terra: [lexical report](<PROJECT_ROOT>/Backend/reports/model_comparison_v1/terra/lexical/lexical_analysis_summary.md), [semantic report](<PROJECT_ROOT>/Backend/reports/model_comparison_v1/terra/semantic/semantic_analysis_summary.md), [40-pair audit with texts and semantic scores](<PROJECT_ROOT>/Backend/reports/model_comparison_v1/terra/semantic/hash_ranked_audit_sample_40_with_semantic.csv).
- Luna: [lexical report](<PROJECT_ROOT>/Backend/reports/model_comparison_v1/luna/lexical/lexical_analysis_summary.md), [semantic report](<PROJECT_ROOT>/Backend/reports/model_comparison_v1/luna/semantic/semantic_analysis_summary.md), [40-pair audit with texts and semantic scores](<PROJECT_ROOT>/Backend/reports/model_comparison_v1/luna/semantic/hash_ranked_audit_sample_40_with_semantic.csv).
- Astra: [lexical report](<PROJECT_ROOT>/Backend/reports/model_comparison_v1/astra/lexical/lexical_analysis_summary.md), [semantic report](<PROJECT_ROOT>/Backend/reports/model_comparison_v1/astra/semantic/semantic_analysis_summary.md), [40-pair audit with texts and semantic scores](<PROJECT_ROOT>/Backend/reports/model_comparison_v1/astra/semantic/hash_ranked_audit_sample_40_with_semantic.csv).

## Limits and next interpretation step

These are four gameplay runs, not controlled identical-prompt replications. Scenario order and rolling previousStorySummary differ. Equal-scenario weighting corrects unequal scenario representation, not history differences or within-run dependence. Pairs reuse texts: 296/288 pair rows are not 296/288 independent experimental observations. No p-values, causal model superiority, quality/creativity ranking, or calibrated high-similarity thresholds are claimed.

Each model's 40-pair audit uses the same proportional SHA-256 ranking method/salt, but different actual pairs. The 40 disagreement field-cases are a separate diagnostic selection and may overlap audit samples. Reading these can explore required facts, paraphrasing, recurring phrases/templates, framing differences, and anomalous output; no qualitative labels have been assigned by this script. A single researcher's inspection is not independent human validation or ground truth.

Requested generation model IDs are recorded in the raw logs; a separate API-returned model ID was not retained. Luna's excluded API connection failure still belongs in any future reliability analysis.

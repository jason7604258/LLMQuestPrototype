# Combined Lexical–Semantic Findings (Frozen 72)

## Scope and status

- Method version: `combined-frozen72-v1`
- Frozen input: first 206 physical JSONL lines
- Input SHA-256: `e24f11761aa490997e4ef9d39a41ffc9da1888940510748237be369329e734ad`
- Generations: 72 across 8 scenarios
- Within-scenario narrative pairs: 296
- Field comparisons: 592
- Formal lexical method: `lexical-field-v3-word`
- Formal semantic method: `semantic-field-v1-mpnet-cosine`
- Legacy character-level SequenceMatcher bands are excluded.

Only introduction and completionText are analyzed, separately. Titles remain visible for inspection but do not enter the lexical or semantic scores. All numerical summaries use all 296 pairs; the 40-pair audit does not estimate overall values.

## Experiment context (not text similarity)

| Generations | OpenAI | Fallbacks | Started | Completed | Completion rate | Mean completion time | Total tokens | Estimated cost |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 72 | 72 | 0 | 72 | 62 | 86.1% | 28.475 s | 80,094 | USD 1.074645 |

Lifecycle records provide started/completed outcomes but are excluded from every lexical and semantic calculation.

## Formal measures

- Token LCS F1: primary ordered lexical overlap.
- Word 3-gram Jaccard: strict supplementary phrase overlap.
- Word 1-gram Jaccard: descriptive vocabulary overlap in source tables.
- MPNet cosine: primary whole-passage semantic similarity.
- Spearman rho: primary cross-metric association; Pearson r: supplementary.
- No score is a percentage, no metrics are averaged into one quality score, and no uncalibrated 80%/85% bands are used.

## Overall within-scenario results

| Field | Pairs | LCS mean | LCS P90 | Word-3 mean | Word-3 P90 | Word-3 zero | Semantic mean | Semantic median | Semantic P90 | Semantic macro mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `introduction` | 296 | 0.3218 | 0.4594 | 0.0479 | 0.1165 | 15.9% | 0.8059 | 0.8137 | 0.8769 | 0.8020 |
| `completionText` | 296 | 0.3601 | 0.5256 | 0.0377 | 0.1111 | 48.3% | 0.6534 | 0.6668 | 0.7998 | 0.6527 |

Completion has higher mean ordered lexical overlap, whereas introduction has higher mean semantic cosine. The score families measure different properties and do not share a common unit.

## Scenario profiles

### `introduction`

| Scenario | Pairs | Semantic mean (rank) | LCS mean (rank) | Word-3 mean (rank) |
|---|---:|---:|---:|---:|
| `slay_caveborn_spider_01` | 21 | 0.8505 (1) | 0.3663 (1) | 0.0886 (1) |
| `slay_caveborn_bear_01` | 45 | 0.8340 (2) | 0.3235 (4) | 0.0544 (3) |
| `slay_caveborn_turtle_01` | 55 | 0.8116 (3) | 0.3444 (2) | 0.0516 (4) |
| `slay_caveborn_snake_01` | 45 | 0.8085 (4) | 0.3003 (7) | 0.0482 (5) |
| `kill_torch_01` | 36 | 0.8060 (5) | 0.3160 (5) | 0.0359 (6) |
| `collect_mushroom_01` | 28 | 0.8059 (6) | 0.3074 (6) | 0.0249 (7) |
| `slay_caveborn_lizard_01` | 45 | 0.7937 (7) | 0.3299 (3) | 0.0564 (2) |
| `slay_torch_boss_01` | 21 | 0.7059 (8) | 0.2720 (8) | 0.0156 (8) |

### `completionText`

| Scenario | Pairs | Semantic mean (rank) | LCS mean (rank) | Word-3 mean (rank) |
|---|---:|---:|---:|---:|
| `slay_caveborn_bear_01` | 45 | 0.7045 (1) | 0.4229 (1) | 0.0591 (1) |
| `slay_torch_boss_01` | 21 | 0.7016 (2) | 0.3396 (6) | 0.0210 (7) |
| `slay_caveborn_turtle_01` | 55 | 0.6529 (3) | 0.3720 (4) | 0.0395 (4) |
| `kill_torch_01` | 36 | 0.6463 (4) | 0.2764 (8) | 0.0099 (8) |
| `collect_mushroom_01` | 28 | 0.6448 (5) | 0.3278 (7) | 0.0389 (5) |
| `slay_caveborn_snake_01` | 45 | 0.6404 (6) | 0.3424 (5) | 0.0316 (6) |
| `slay_caveborn_lizard_01` | 45 | 0.6283 (7) | 0.3733 (3) | 0.0471 (2) |
| `slay_caveborn_spider_01` | 21 | 0.6026 (8) | 0.4109 (2) | 0.0427 (3) |

Ranks compare only the eight observed scenarios. Rank 1 means the highest observed mean for that metric, not the best narrative quality.

## Cross-field findings

- Introduction semantic cosine exceeds completion in 8/8 scenarios.
- Completion Token LCS F1 exceeds introduction in 7/8 scenarios.
- `introduction` semantic mean is highest for `slay_caveborn_spider_01` (0.8505) and lowest for `slay_torch_boss_01` (0.7059).
- `introduction` LCS mean is highest for `slay_caveborn_spider_01` (0.3663).
- `completionText` semantic mean is highest for `slay_caveborn_bear_01` (0.7045) and lowest for `slay_caveborn_spider_01` (0.6026).
- `completionText` LCS mean is highest for `slay_caveborn_bear_01` (0.4229).

## Lexical–semantic association

| Field | Lexical measure | Pairs | Spearman rho | Pearson r |
|---|---|---:|---:|---:|
| `introduction` | `tokenLcsF1` | 296 | 0.4556 | 0.4510 |
| `introduction` | `word3gramJaccard` | 296 | 0.4496 | 0.3920 |
| `introduction` | `word1gramJaccard` | 296 | 0.5525 | 0.5265 |
| `completionText` | `tokenLcsF1` | 296 | 0.6035 | 0.6017 |
| `completionText` | `word3gramJaccard` | 296 | 0.5150 | 0.5143 |
| `completionText` | `word1gramJaccard` | 296 | 0.5947 | 0.6000 |

All pair-level associations are positive, but none establishes equivalence between lexical and semantic measures. Pairs reuse narratives and may contain scenario-level differences, so ordinary independent-observation p-values are omitted.

### Equal-scenario sensitivity

This sensitivity calculation first reduces each field and scenario to one mean, then compares the rankings of the eight scenario means. It prevents scenarios with more pairs from receiving more weight, but n=8 is small, so the values remain descriptive.

| Field | Lexical measure | Scenarios | Spearman rho |
|---|---|---:|---:|
| `introduction` | `tokenLcsF1` | 8 | 0.6429 |
| `introduction` | `word3gramJaccard` | 8 | 0.6429 |
| `introduction` | `word1gramJaccard` | 8 | 0.5952 |
| `completionText` | `tokenLcsF1` | 8 | -0.0714 |
| `completionText` | `word3gramJaccard` | 8 | -0.0952 |
| `completionText` | `word1gramJaccard` | 8 | 0.1667 |

Introduction scenario means show positive semantic–lexical rank agreement. Completion scenario means show little agreement between semantic cosine and LCS/Word-3, even though the corresponding pair-level associations are positive. The level of analysis therefore changes the conclusion, and both views are retained.

## Pair-level rank-disagreement candidates

Within each field, semantic cosine and Token LCS F1 are converted separately to average-rank percentiles across the same 296 pairs. Their gap surfaces cases where one measure ranks a pair much higher. This is dataset-relative case discovery, not a quality threshold and not automatic proof of paraphrasing or repetition.

### `introduction`: semantic rank most exceeds LCS rank

| Scenario | Pair | Semantic | Semantic pct. | LCS F1 | LCS pct. | Rank gap | Word-3 J | Titles |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `slay_caveborn_snake_01` | `1ff7bb96… / c1fa090c…` | 0.8948 | 0.9661 | 0.2034 | 0.0576 | 0.9085 | 0.0185 | Coils Along the Old Road / Bands in the Dark |
| `collect_mushroom_01` | `0bde6c42… / d332afcc…` | 0.8607 | 0.8102 | 0.2121 | 0.0797 | 0.7305 | 0.0000 | Spores Among the Stones / Glow Among the Ruins |
| `slay_caveborn_snake_01` | `1ff7bb96… / 3b152581…` | 0.8829 | 0.9254 | 0.2456 | 0.2271 | 0.6983 | 0.1042 | Coils Along the Old Road / Fangs in the Western Rocks |

### `introduction`: LCS rank most exceeds semantic rank

| Scenario | Pair | Semantic | Semantic pct. | LCS F1 | LCS pct. | Rank gap | Word-3 J | Titles |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `kill_torch_01` | `71960381… / 89935b1f…` | 0.7023 | 0.0542 | 0.3934 | 0.7864 | 0.7322 | 0.1176 | Embers in the Mountain Arena / Flames in the Empty Arena |
| `slay_caveborn_lizard_01` | `e236c99f… / ff569c41…` | 0.7307 | 0.1220 | 0.3614 | 0.7119 | 0.5898 | 0.0822 | Crests by the Western Cave / Crests Among the Ruins |
| `slay_torch_boss_01` | `264863e7… / ad0c649f…` | 0.7743 | 0.2644 | 0.4242 | 0.8542 | 0.5898 | 0.0508 | The Last Flame of the Arena / The Last Flame of the Arena |

### `completionText`: semantic rank most exceeds LCS rank

| Scenario | Pair | Semantic | Semantic pct. | LCS F1 | LCS pct. | Rank gap | Word-3 J | Titles |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `kill_torch_01` | `1f53cf34… / 61e755d4…` | 0.8015 | 0.9017 | 0.1961 | 0.0746 | 0.8271 | 0.0000 | Embers in the Mountain Arena / Firelight in the Empty Arena |
| `collect_mushroom_01` | `7eafe283… / c3559d40…` | 0.7851 | 0.8780 | 0.2000 | 0.0780 | 0.8000 | 0.0000 | Spores Among the Stones / Spores in the Silent Ring |
| `collect_mushroom_01` | `33e8c7e9… / d332afcc…` | 0.7379 | 0.7661 | 0.1290 | 0.0085 | 0.7576 | 0.0000 | Glow Among the Ruins / Glow Among the Ruins |

### `completionText`: LCS rank most exceeds semantic rank

| Scenario | Pair | Semantic | Semantic pct. | LCS F1 | LCS pct. | Rank gap | Word-3 J | Titles |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `slay_caveborn_spider_01` | `0004c413… / cb686e46…` | 0.5553 | 0.2136 | 0.5714 | 0.9356 | 0.7220 | 0.0333 | Eyes Along the Old Road / Eyes Along the Old Road |
| `slay_caveborn_spider_01` | `0004c413… / 2ffc2610…` | 0.5399 | 0.1797 | 0.5000 | 0.8780 | 0.6983 | 0.0000 | Eyes Along the Old Road / Eyes in the Western Rocks |
| `slay_caveborn_spider_01` | `2ffc2610… / cb686e46…` | 0.5562 | 0.2203 | 0.4848 | 0.8644 | 0.6441 | 0.0000 | Eyes in the Western Rocks / Eyes Along the Old Road |

## Fixed 40-pair qualitative audit

Allocation: `collect_mushroom_01`=4, `kill_torch_01`=5, `slay_caveborn_bear_01`=6, `slay_caveborn_lizard_01`=6, `slay_caveborn_snake_01`=6, `slay_caveborn_spider_01`=3, `slay_caveborn_turtle_01`=7, `slay_torch_boss_01`=3.

Within each scenario, every candidate receives SHA-256(20260820|scenarioId|requestIdA|requestIdB), is sorted by that hash, and the first allocated number is retained. Therefore "same ranking positions" means the same first hash-ranked positions, not the highest similarity scores. The semantic audit preserves all 40 original rows, IDs, hashes, and order before appending cosine.

The audit supports example inspection only. It is not human validation, does not calibrate thresholds, and does not calculate the reported means or correlations.

## Defensible interpretation

1. No exact normalized introduction or completion duplicates were observed, although ordered word and phrase overlap remains measurable.
2. Introduction passages are closer in whole-passage semantic space on average, consistent with strong shared scenario content; this alone does not establish poor creativity.
3. Completion passages have higher mean Token LCS F1 despite lower mean semantic cosine, which supports keeping wording and meaning separate.
4. Positive but imperfect Spearman associations and the rank-gap cases show that neither score family subsumes the other.
5. Scenario rankings describe these fixed outputs, not intrinsic properties of enemies or human judgments of quality.

## Limits and next use

- Same-scenario texts necessarily share enemies, locations, actions, and continuity facts.
- MPNet is a general-English model, not a calibrated fantasy-creativity judge.
- Pair rows are dependent because every narrative enters several pairs.
- Without human-labelled ground truth, no high/review cutoff or classification accuracy is claimed.
- MiniLM may later provide a model-sensitivity check; MPNet remains primary.

The next analytical task is a transparent reading of the fixed 40-pair audit and rank-gap cases, recording shared required facts, paraphrasing, repeated templates, different framing, and anomalies without turning these observations into unvalidated labels.

## Reproducibility fingerprints

- Lexical analyzer SHA-256: `9f88982a0e2a2aa2a46c6bdf8c9b082b9efef071659abad2c8f06eb22cdfd53c`
- Semantic analyzer SHA-256: `168c6ae7596bb6ad41c3d6f849a68274b5f02e34278fe301d81019025ef7e4e3`
- lexical summary SHA-256: `5e2f14dbf6b94cdf0aff9199b93138836764f9520ffb363d039fe00df09ebf5e`
- lexical pairs SHA-256: `79d5cfc9a95490de12e66087499d1f9e055e31c84a8863c0e702358906d29d7a`
- lexical audit SHA-256: `1dc5472400c157bcb6bb6f0374c6496c8d928809d14780ebf9878d5b3a2efc3d`
- semantic summary SHA-256: `8ae37adf2d677c610fe49ad87b357c6d7e40cf276ab327826bb2b2c5a614f09c`
- semantic pairs SHA-256: `b050e1a6ea403be5f38049e784d6d5d6907e3b83a9e08a57f844816a7523969f`
- correlations SHA-256: `b05e75d0d08ac48440283e5f68c39b8d6b8889d3bcafc541ac9979cf998e5f4a`
- semantic audit SHA-256: `177647baf57ef91a9e362a258a29ca64de24ed14274057db2960ce0d310f2b13`
- generation records SHA-256: `8ae0231a68c7d7595fbe01815a215708a2ed62361c0580980d56bc221399c618`
- combined analyzer SHA-256: `2a6e41a12b4889097116aa46b118112e8e6bd914204a6754faee1635787784e7`

# Word-level Lexical Analysis (72 generations)

## Dataset

- Input: `<PROJECT_ROOT>/Backend/logs/demo_narrative_runs_2026-08-20_take01.jsonl`
- Physical-line prefix: 206
- Prefix SHA-256: `e24f11761aa490997e4ef9d39a41ffc9da1888940510748237be369329e734ad`
- Expected prefix SHA-256: `e24f11761aa490997e4ef9d39a41ffc9da1888940510748237be369329e734ad`
- Prefix hash verified: true
- Parsed JSON-object records: 206
- Malformed/non-object records skipped: 0
- Generation records: 72
- Within-scenario narrative pairs: 296
- Field-level comparisons: 592

## Method

Text is normalized with Unicode NFKC and case folding; runs of non-word characters and underscores are replaced with spaces, whitespace is collapsed, and the result is split into word tokens. `introduction` and `completionText` are compared separately. Only pairs with the same exact non-empty `scenarioId` enter this primary analysis.

- **Symmetric Token LCS F1 (ROUGE-L-style)** is the primary ordered overlap metric: `2 × LCS length / (tokens A + tokens B)`. LCS preserves relative word order but allows gaps; it is not a standard ROUGE score with reference/candidate direction.
- **Word 3-gram Jaccard** compares sets of unique contiguous word triples. It is a strict supplementary phrase-overlap metric and ignores frequency.
  It is undefined if neither text contains a word triple; zero-rate denominators include only pairs with a defined 3-gram score.
- **Word 1-gram Jaccard** compares sets of unique words. It describes vocabulary overlap but ignores word order and frequency.
- Numbers are retained. No stopwords, stemming, or lemmatization are used, and no uncalibrated high/review thresholds are assigned.
- P90 uses linear interpolation at position `(n - 1) × 0.90`.
- Magnitudes are not directly comparable between the three metrics. Completion texts are also shorter and more constrained than introductions.
- Scores describe wording overlap, not semantic similarity or narrative quality.

## Overall within-scenario results (pooled pair-weighted)

| Field | Pairs | Word-1 J mean | Word-1 J P90 | Token LCS F1 mean | Token LCS F1 P90 | Word-3 J mean | Word-3 J P90 | Word-3 zero | Exact |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `introduction` | 296 | 0.2738 | 0.3738 | 0.3218 | 0.4594 | 0.0479 | 0.1165 | 47 (15.9%) | 0 |
| `completionText` | 296 | 0.2200 | 0.3636 | 0.3601 | 0.5256 | 0.0377 | 0.1111 | 143 (48.3%) | 0 |

## Per-scenario results

| Scenario | Field | Pairs | Word-1 J mean | Token LCS F1 mean | Token LCS F1 P90 | Token LCS F1 max | Word-3 J mean | Word-3 zero |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `collect_mushroom_01` | `introduction` | 28 | 0.2697 | 0.3074 | 0.4144 | 0.5172 | 0.0249 | 46.4% |
| `collect_mushroom_01` | `completionText` | 28 | 0.1889 | 0.3278 | 0.5100 | 0.6286 | 0.0389 | 60.7% |
| `kill_torch_01` | `introduction` | 36 | 0.2362 | 0.3160 | 0.4602 | 0.5970 | 0.0359 | 13.9% |
| `kill_torch_01` | `completionText` | 36 | 0.1621 | 0.2764 | 0.4069 | 0.5714 | 0.0099 | 75.0% |
| `slay_caveborn_bear_01` | `introduction` | 45 | 0.2773 | 0.3235 | 0.4545 | 0.5333 | 0.0544 | 13.3% |
| `slay_caveborn_bear_01` | `completionText` | 45 | 0.2715 | 0.4229 | 0.6015 | 0.7333 | 0.0591 | 20.0% |
| `slay_caveborn_lizard_01` | `introduction` | 45 | 0.2980 | 0.3299 | 0.4674 | 0.7273 | 0.0564 | 8.9% |
| `slay_caveborn_lizard_01` | `completionText` | 45 | 0.2295 | 0.3733 | 0.5384 | 0.8824 | 0.0471 | 44.4% |
| `slay_caveborn_snake_01` | `introduction` | 45 | 0.2620 | 0.3003 | 0.4232 | 0.5758 | 0.0482 | 11.1% |
| `slay_caveborn_snake_01` | `completionText` | 45 | 0.1952 | 0.3424 | 0.4603 | 0.5294 | 0.0316 | 48.9% |
| `slay_caveborn_spider_01` | `introduction` | 21 | 0.2981 | 0.3663 | 0.4865 | 0.5974 | 0.0886 | 0.0% |
| `slay_caveborn_spider_01` | `completionText` | 21 | 0.2612 | 0.4109 | 0.5714 | 0.6486 | 0.0427 | 33.3% |
| `slay_caveborn_turtle_01` | `introduction` | 55 | 0.3018 | 0.3444 | 0.4969 | 0.5938 | 0.0516 | 7.3% |
| `slay_caveborn_turtle_01` | `completionText` | 55 | 0.2162 | 0.3720 | 0.5428 | 0.6875 | 0.0395 | 45.5% |
| `slay_torch_boss_01` | `introduction` | 21 | 0.2122 | 0.2720 | 0.3492 | 0.4242 | 0.0156 | 47.6% |
| `slay_torch_boss_01` | `completionText` | 21 | 0.2520 | 0.3396 | 0.4324 | 0.5217 | 0.0210 | 76.2% |

## Highest Token LCS F1 pairs

| Field | Rank | Score | Scenario | Title A | Title B | Request A | Request B |
|---|---:|---:|---|---|---|---|---|
| `introduction` | 1 | 0.7273 | `slay_caveborn_lizard_01` | Cre，sts by the Old Road | Crests by the Western Cave | `38049414cb684cfdb76cf1ea484f7bcb` | `e236c99fd8ba4b718ad9fcf765822723` |
| `introduction` | 2 | 0.5974 | `slay_caveborn_spider_01` | Eyes Along the Old Road | Eyes Along the Old Road | `82a08efbb67b49549155bdbae108302c` | `cb686e46ecfe424b9ffbe0ff114fdf19` |
| `introduction` | 3 | 0.5970 | `kill_torch_01` | Embers in the Mountain Arena | Lights in the Lost Arena | `1f53cf34c8844802bc379ed2eb31e9b9` | `27a7f80b305c42b7a3c653fa4a3fb480` |
| `introduction` | 4 | 0.5938 | `slay_caveborn_turtle_01` | The Spiral Shell | The Spiral Shell | `461350b1fa704438a9aea53488901831` | `7836c20f09e64bb69f1b544c4b45d903` |
| `introduction` | 5 | 0.5846 | `slay_caveborn_turtle_01` | The Spiral in Stone | The Spiral in the Stone | `477031fdb9304e4f965335391bc21f06` | `cc4db7a70efe4f589947c86a56fc990f` |
| `completionText` | 1 | 0.8824 | `slay_caveborn_lizard_01` | Cre，sts by the Old Road | Crests Among the Ruins | `38049414cb684cfdb76cf1ea484f7bcb` | `7d091825d2a54b52aca66e0029009c47` |
| `completionText` | 2 | 0.7333 | `slay_caveborn_bear_01` | Claws by the Western Cave | Claws in the Ruins | `a9f59444dca34b9baac02c90a0082a08` | `e82f128a419d4be3b85fe145aa5ef3d5` |
| `completionText` | 3 | 0.6875 | `slay_caveborn_lizard_01` | Cre rests Among the Ruins | Crests Among the Ruins | `39d6a848b4b64697a5abb4928193eee3` | `7d091825d2a54b52aca66e0029009c47` |
| `completionText` | 4 | 0.6875 | `slay_caveborn_turtle_01` | The Spiral in Stone | The Spiral Shell | `477031fdb9304e4f965335391bc21f06` | `630250d3a38e48f581f253ea12827f20` |
| `completionText` | 5 | 0.6857 | `slay_caveborn_bear_01` | Claws by the Western Rocks | Claws Among the Ruins | `6db97ea99d5d42ada490241797be9d62` | `cda61949cac4437d88ecaad238601b9d` |

## Reproducible audit sample

The audit CSV contains 40 unique narrative pairs. It uses proportional scenario strata and deterministic SHA-256 ranking with fixed salt `20260820`. Selection did not use similarity scores or score bands.

The 40 rows are a qualitative inspection set, **not** human validation. All 296 pairs are used for the numerical analysis. Pair scores are not statistically independent because one narrative participates in multiple pairs; the report therefore presents descriptive statistics only.

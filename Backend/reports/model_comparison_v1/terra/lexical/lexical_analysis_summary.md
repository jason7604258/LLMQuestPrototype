# Word-level Lexical Analysis (72 generations)

## Dataset

- Input: `<PROJECT_ROOT>/Backend/reports/model_comparison_v1/terra/input_frozen72.jsonl`
- Physical-line prefix: 216
- Prefix SHA-256: `2db1a0430dc58316d6419db420980d4c48468fad8b003b799ae36b30f1c13b1b`
- Expected prefix SHA-256: `2db1a0430dc58316d6419db420980d4c48468fad8b003b799ae36b30f1c13b1b`
- Prefix hash verified: true
- Parsed JSON-object records: 216
- Malformed/non-object records skipped: 0
- Generation records: 72
- Within-scenario narrative pairs: 288
- Field-level comparisons: 576

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
| `introduction` | 288 | 0.2383 | 0.3504 | 0.2962 | 0.4366 | 0.0316 | 0.0755 | 78 (27.1%) | 0 |
| `completionText` | 288 | 0.2206 | 0.3515 | 0.3521 | 0.5143 | 0.0338 | 0.0977 | 149 (51.7%) | 0 |

## Per-scenario results

| Scenario | Field | Pairs | Word-1 J mean | Token LCS F1 mean | Token LCS F1 P90 | Token LCS F1 max | Word-3 J mean | Word-3 zero |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `collect_mushroom_01` | `introduction` | 36 | 0.2572 | 0.3194 | 0.4357 | 0.5312 | 0.0274 | 30.6% |
| `collect_mushroom_01` | `completionText` | 36 | 0.1950 | 0.3357 | 0.4571 | 0.5625 | 0.0191 | 63.9% |
| `kill_torch_01` | `introduction` | 36 | 0.2226 | 0.3272 | 0.4864 | 0.5588 | 0.0388 | 30.6% |
| `kill_torch_01` | `completionText` | 36 | 0.3114 | 0.4348 | 0.5844 | 0.6875 | 0.0715 | 33.3% |
| `slay_caveborn_bear_01` | `introduction` | 36 | 0.2199 | 0.2821 | 0.3678 | 0.5000 | 0.0335 | 22.2% |
| `slay_caveborn_bear_01` | `completionText` | 36 | 0.2392 | 0.3971 | 0.5242 | 0.5600 | 0.0433 | 30.6% |
| `slay_caveborn_lizard_01` | `introduction` | 36 | 0.2151 | 0.2666 | 0.3598 | 0.4211 | 0.0237 | 25.0% |
| `slay_caveborn_lizard_01` | `completionText` | 36 | 0.1727 | 0.3069 | 0.4218 | 0.7059 | 0.0271 | 58.3% |
| `slay_caveborn_snake_01` | `introduction` | 36 | 0.2341 | 0.2815 | 0.4232 | 0.5397 | 0.0362 | 19.4% |
| `slay_caveborn_snake_01` | `completionText` | 36 | 0.1922 | 0.3170 | 0.4824 | 0.5778 | 0.0282 | 63.9% |
| `slay_caveborn_spider_01` | `introduction` | 36 | 0.2328 | 0.2776 | 0.3977 | 0.5397 | 0.0246 | 33.3% |
| `slay_caveborn_spider_01` | `completionText` | 36 | 0.2138 | 0.3201 | 0.4590 | 0.6154 | 0.0254 | 58.3% |
| `slay_caveborn_turtle_01` | `introduction` | 36 | 0.2645 | 0.2881 | 0.4147 | 0.4923 | 0.0408 | 19.4% |
| `slay_caveborn_turtle_01` | `completionText` | 36 | 0.1721 | 0.2988 | 0.3896 | 0.4516 | 0.0196 | 52.8% |
| `slay_torch_boss_01` | `introduction` | 36 | 0.2599 | 0.3271 | 0.4426 | 0.5000 | 0.0278 | 36.1% |
| `slay_torch_boss_01` | `completionText` | 36 | 0.2681 | 0.4062 | 0.5916 | 0.7000 | 0.0364 | 52.8% |

## Highest Token LCS F1 pairs

| Field | Rank | Score | Scenario | Title A | Title B | Request A | Request B |
|---|---:|---:|---|---|---|---|---|
| `introduction` | 1 | 0.5588 | `kill_torch_01` | Lights in the Mountain Arena | Lanterns in the Mountain Arena | `512b469e47ec46d193da3101b7b81e80` | `8f4d2906f16848eba0aef6d7da213e87` |
| `introduction` | 2 | 0.5574 | `kill_torch_01` | Lights in the Mountain Arena | Embers in the Open Arena | `512b469e47ec46d193da3101b7b81e80` | `c379082ef386419a89c75b7c53d9960d` |
| `introduction` | 3 | 0.5397 | `slay_caveborn_snake_01` | Echoes in the Western Cave | Stirrings in the Western Rocks | `900b74340c3d4ef8a6a5719574afa3b5` | `9833f4dd3cd443c3b8b3dd3164ed4f6c` |
| `introduction` | 4 | 0.5397 | `slay_caveborn_spider_01` | Eyes in the Western Grotto | Eyes in the Stone | `7970fe29753a4b4c910a3bab81fe4c28` | `cffc768876af469bb3839117fdf412b7` |
| `introduction` | 5 | 0.5312 | `collect_mushroom_01` | Spores in the Ruins | Lanterncaps Among the Ruins | `b4fc196c68da484daa08dd1074d7895e` | `c0046fc7f8004b90bd4c3c486684194c` |
| `completionText` | 1 | 0.7059 | `slay_caveborn_lizard_01` | Crests in the Western Dark | Crests at the Cave Mouth | `1c1f9df72ebc4a3da516e6736d2f6749` | `504ab5537653453f92dfd87f88625d6a` |
| `completionText` | 2 | 0.7000 | `slay_torch_boss_01` | The Last Arena Flame | The Arena’s Last Flame | `0e83cd86e85444dc875a4ed3a4fd24b8` | `75d27ce875e5482fb8f9324accd50ac5` |
| `completionText` | 3 | 0.6875 | `kill_torch_01` | Lights in the Mountain Arena | Embers in the Open Arena | `512b469e47ec46d193da3101b7b81e80` | `c379082ef386419a89c75b7c53d9960d` |
| `completionText` | 4 | 0.6667 | `slay_torch_boss_01` | The Last Arena Flame | The Arena’s Last Light | `0e83cd86e85444dc875a4ed3a4fd24b8` | `5d3bcdd0106d454b9986caf2571e3084` |
| `completionText` | 5 | 0.6667 | `slay_torch_boss_01` | The Arena’s Last Light | The Arena’s Last Flame | `5d3bcdd0106d454b9986caf2571e3084` | `75d27ce875e5482fb8f9324accd50ac5` |

## Reproducible audit sample

The audit CSV contains 40 unique narrative pairs. It uses proportional scenario strata and deterministic SHA-256 ranking with fixed salt `20260820`. Selection did not use similarity scores or score bands.

The 40 rows are a qualitative inspection set, **not** human validation. All 288 pairs are used for the numerical analysis. Pair scores are not statistically independent because one narrative participates in multiple pairs; the report therefore presents descriptive statistics only.

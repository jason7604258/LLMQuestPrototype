# Word-level Lexical Analysis (72 generations)

## Dataset

- Input: `<PROJECT_ROOT>/Backend/reports/model_comparison_v1/luna/input_frozen72.jsonl`
- Physical-line prefix: 216
- Prefix SHA-256: `5f05b7b1e96ab17de58b89cd9bcad3f23f62eba9b8a1571dcd60d2b79940c568`
- Expected prefix SHA-256: `5f05b7b1e96ab17de58b89cd9bcad3f23f62eba9b8a1571dcd60d2b79940c568`
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
| `introduction` | 288 | 0.2664 | 0.3851 | 0.3264 | 0.4606 | 0.0514 | 0.1202 | 59 (20.5%) | 0 |
| `completionText` | 288 | 0.2263 | 0.3514 | 0.3558 | 0.5091 | 0.0411 | 0.0930 | 68 (23.6%) | 0 |

## Per-scenario results

| Scenario | Field | Pairs | Word-1 J mean | Token LCS F1 mean | Token LCS F1 P90 | Token LCS F1 max | Word-3 J mean | Word-3 zero |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `collect_mushroom_01` | `introduction` | 36 | 0.2699 | 0.3296 | 0.4627 | 0.5965 | 0.0417 | 36.1% |
| `collect_mushroom_01` | `completionText` | 36 | 0.1726 | 0.2759 | 0.4037 | 0.5128 | 0.0322 | 41.7% |
| `kill_torch_01` | `introduction` | 36 | 0.2565 | 0.3285 | 0.4676 | 0.6866 | 0.0373 | 36.1% |
| `kill_torch_01` | `completionText` | 36 | 0.2296 | 0.3696 | 0.5000 | 0.5926 | 0.0421 | 25.0% |
| `slay_caveborn_bear_01` | `introduction` | 36 | 0.2733 | 0.3289 | 0.4853 | 0.5429 | 0.0754 | 2.8% |
| `slay_caveborn_bear_01` | `completionText` | 36 | 0.2670 | 0.3943 | 0.4953 | 0.5283 | 0.0427 | 0.0% |
| `slay_caveborn_lizard_01` | `introduction` | 36 | 0.2545 | 0.3228 | 0.4344 | 0.6885 | 0.0546 | 13.9% |
| `slay_caveborn_lizard_01` | `completionText` | 36 | 0.2371 | 0.3792 | 0.5049 | 0.6316 | 0.0461 | 0.0% |
| `slay_caveborn_snake_01` | `introduction` | 36 | 0.2696 | 0.3355 | 0.5042 | 0.6667 | 0.0644 | 22.2% |
| `slay_caveborn_snake_01` | `completionText` | 36 | 0.1805 | 0.2818 | 0.4194 | 0.6818 | 0.0270 | 47.2% |
| `slay_caveborn_spider_01` | `introduction` | 36 | 0.2589 | 0.3406 | 0.4722 | 0.6122 | 0.0537 | 11.1% |
| `slay_caveborn_spider_01` | `completionText` | 36 | 0.2238 | 0.3651 | 0.4509 | 0.8235 | 0.0396 | 25.0% |
| `slay_caveborn_turtle_01` | `introduction` | 36 | 0.2805 | 0.3037 | 0.4191 | 0.5797 | 0.0507 | 11.1% |
| `slay_caveborn_turtle_01` | `completionText` | 36 | 0.2112 | 0.3577 | 0.4496 | 0.6071 | 0.0352 | 11.1% |
| `slay_torch_boss_01` | `introduction` | 36 | 0.2679 | 0.3215 | 0.4218 | 0.4857 | 0.0339 | 30.6% |
| `slay_torch_boss_01` | `completionText` | 36 | 0.2883 | 0.4224 | 0.6158 | 0.7368 | 0.0638 | 38.9% |

## Highest Token LCS F1 pairs

| Field | Rank | Score | Scenario | Title A | Title B | Request A | Request B |
|---|---:|---:|---|---|---|---|---|
| `introduction` | 1 | 0.6885 | `slay_caveborn_lizard_01` | Crests Beneath the Ruins | Crests Beneath the Ruins | `2ff34069fd8b447bbe1ecd41c4398f3d` | `aec11dd626ac49e1912e756b2474941d` |
| `introduction` | 2 | 0.6866 | `kill_torch_01` | Torches in the Open Air | Lights in the Ruins | `6726c5f7d00e40edb749fc0be022ab2d` | `c84b1ba69ae446619a41055a692f39fb` |
| `introduction` | 3 | 0.6667 | `slay_caveborn_snake_01` | Echoes Beneath the Western Rocks | The Serpents Beneath the Ruins | `60cb5dd655fb424bb808c0bbd87e8d7d` | `965f2be42eb741ee9770f8cc8374d652` |
| `introduction` | 4 | 0.6122 | `slay_caveborn_spider_01` | Eyes Beneath the Western Rocks | Shadows Beneath the Western Rocks | `d79ac35e1ac244deb87eaaa967533555` | `dd28a415a06f4f819863c9982957e1bd` |
| `introduction` | 5 | 0.5965 | `collect_mushroom_01` | Glow Beneath the Ruins | Glow Beneath the Ruins | `476497ca73394459bcecb3750c3c4497` | `638fffd263fc43ec804fe229f42c325f` |
| `completionText` | 1 | 0.8235 | `slay_caveborn_spider_01` | Eyes Beneath the Fallen Road | Eyes Beneath the Ruins | `404a2119c3764cffa42500f36124f347` | `eb0fef25caa74ea88bc0fdf341786eb2` |
| `completionText` | 2 | 0.7368 | `slay_torch_boss_01` | The Last Flame of the Arena | The Last Flame of the Arena | `823b828a2e1c460098b7eaf6e69a127a` | `d551fd878ca046a2ada939f6fab368c2` |
| `completionText` | 3 | 0.6818 | `slay_caveborn_snake_01` | Fangs Beneath the Fallen Road | Fangs Beneath the Western Rocks | `3a2ff770903a48649400b24804b9e0c5` | `f5c3e33473fd40b79982208207174a64` |
| `completionText` | 4 | 0.6786 | `slay_caveborn_spider_01` | Eyes Beneath the Western Rocks | Eyes Beneath the Ruins | `e48a6de0ca804ad1a24207b399476991` | `eb0fef25caa74ea88bc0fdf341786eb2` |
| `completionText` | 5 | 0.6441 | `slay_torch_boss_01` | The Last Flame of the Arena | The Last Flame in the Arena | `823b828a2e1c460098b7eaf6e69a127a` | `c261543583ee402287f2d1cf96783789` |

## Reproducible audit sample

The audit CSV contains 40 unique narrative pairs. It uses proportional scenario strata and deterministic SHA-256 ranking with fixed salt `20260820`. Selection did not use similarity scores or score bands.

The 40 rows are a qualitative inspection set, **not** human validation. All 288 pairs are used for the numerical analysis. Pair scores are not statistically independent because one narrative participates in multiple pairs; the report therefore presents descriptive statistics only.

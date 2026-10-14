# Word-level Lexical Analysis (72 generations)

## Dataset

- Input: `<PROJECT_ROOT>/Backend/reports/model_comparison_v1/astra/input_frozen72.jsonl`
- Physical-line prefix: 216
- Prefix SHA-256: `0c8529814f8adfae0100bc769964939be1cb8882f5376ce9ae05edae78f6a440`
- Expected prefix SHA-256: `0c8529814f8adfae0100bc769964939be1cb8882f5376ce9ae05edae78f6a440`
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
| `introduction` | 288 | 0.3171 | 0.4364 | 0.3784 | 0.5289 | 0.0727 | 0.1413 | 26 (9.0%) | 0 |
| `completionText` | 288 | 0.2727 | 0.4375 | 0.3582 | 0.5269 | 0.0579 | 0.1379 | 76 (26.4%) | 0 |

## Per-scenario results

| Scenario | Field | Pairs | Word-1 J mean | Token LCS F1 mean | Token LCS F1 P90 | Token LCS F1 max | Word-3 J mean | Word-3 zero |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `collect_mushroom_01` | `introduction` | 36 | 0.3277 | 0.4012 | 0.5033 | 0.7711 | 0.1012 | 0.0% |
| `collect_mushroom_01` | `completionText` | 36 | 0.1921 | 0.2998 | 0.4176 | 0.5417 | 0.0356 | 55.6% |
| `kill_torch_01` | `introduction` | 36 | 0.2176 | 0.2795 | 0.4264 | 0.6000 | 0.0430 | 27.8% |
| `kill_torch_01` | `completionText` | 36 | 0.1633 | 0.2353 | 0.3235 | 0.3922 | 0.0127 | 66.7% |
| `slay_caveborn_bear_01` | `introduction` | 36 | 0.3312 | 0.3840 | 0.4939 | 0.5823 | 0.0762 | 0.0% |
| `slay_caveborn_bear_01` | `completionText` | 36 | 0.4034 | 0.4668 | 0.5661 | 0.7500 | 0.1144 | 0.0% |
| `slay_caveborn_lizard_01` | `introduction` | 36 | 0.4301 | 0.4845 | 0.6392 | 0.7312 | 0.1181 | 0.0% |
| `slay_caveborn_lizard_01` | `completionText` | 36 | 0.2293 | 0.3284 | 0.4440 | 0.5161 | 0.0410 | 11.1% |
| `slay_caveborn_snake_01` | `introduction` | 36 | 0.3008 | 0.3667 | 0.5180 | 0.6133 | 0.0549 | 19.4% |
| `slay_caveborn_snake_01` | `completionText` | 36 | 0.3642 | 0.4502 | 0.6534 | 0.7241 | 0.0935 | 5.6% |
| `slay_caveborn_spider_01` | `introduction` | 36 | 0.3220 | 0.3692 | 0.4551 | 0.6304 | 0.0569 | 2.8% |
| `slay_caveborn_spider_01` | `completionText` | 36 | 0.2854 | 0.3656 | 0.4950 | 0.5965 | 0.0562 | 5.6% |
| `slay_caveborn_turtle_01` | `introduction` | 36 | 0.3160 | 0.3972 | 0.4727 | 0.5526 | 0.0800 | 0.0% |
| `slay_caveborn_turtle_01` | `completionText` | 36 | 0.3154 | 0.4213 | 0.5988 | 0.7451 | 0.0816 | 16.7% |
| `slay_torch_boss_01` | `introduction` | 36 | 0.2915 | 0.3450 | 0.4824 | 0.5854 | 0.0517 | 22.2% |
| `slay_torch_boss_01` | `completionText` | 36 | 0.2287 | 0.2981 | 0.4374 | 0.5532 | 0.0285 | 50.0% |

## Highest Token LCS F1 pairs

| Field | Rank | Score | Scenario | Title A | Title B | Request A | Request B |
|---|---:|---:|---|---|---|---|---|
| `introduction` | 1 | 0.7711 | `collect_mushroom_01` | A Quiet Kind of Light | A Quiet Return | `355b28e559e04e45a231dde736928994` | `36150134a70e4174a53840ab32aa88a6` |
| `introduction` | 2 | 0.7312 | `slay_caveborn_lizard_01` | Yellow Crests in the Green | Yellow Crests on the Old Road | `03618e0d1bac4dafad18ecf2f8189d62` | `105d602caec847a986bdced097981211` |
| `introduction` | 3 | 0.6667 | `slay_caveborn_lizard_01` | Yellow Crests in the Green | Yellow Crests Among the Ruins | `03618e0d1bac4dafad18ecf2f8189d62` | `8f517310b5fc4d4b9385ac3bedcd1d11` |
| `introduction` | 4 | 0.6667 | `slay_caveborn_lizard_01` | Yellow Crests in the Green | Yellow Crests on the Old Road | `03618e0d1bac4dafad18ecf2f8189d62` | `e5c2d84ebaff4b8c8ef62274f2b15881` |
| `introduction` | 5 | 0.6598 | `slay_caveborn_lizard_01` | Yellow Crests on the Old Road | Yellow Crests on the Old Road | `105d602caec847a986bdced097981211` | `e5c2d84ebaff4b8c8ef62274f2b15881` |
| `completionText` | 1 | 0.7500 | `slay_caveborn_bear_01` | Claws on the Old Road | Claws Along the Old Road | `c759152035c94eb6a11dcfd0d9f2277a` | `d396dd11b68a4a26bb4399c1be6b7a79` |
| `completionText` | 2 | 0.7451 | `slay_caveborn_turtle_01` | Spirals Among the Ruins | Spirals Beneath the Moss | `3b33a8736c794d4b8decc6b1b812df97` | `888c676e31104fcab654039d03aa229f` |
| `completionText` | 3 | 0.7241 | `slay_caveborn_snake_01` | Coils Among the Ruins | Orange Among the Shadows | `0dd930902d394a819209d2af37a528bb` | `a38a554027134985b995e0e6839ae92c` |
| `completionText` | 4 | 0.7213 | `slay_caveborn_snake_01` | Along the Old Road | Orange Against the Shadows | `affaa0767b0d44e3b06a0cbbc012a0a7` | `cfede3de33cb4491a677ff1eedd20d1f` |
| `completionText` | 5 | 0.6984 | `slay_caveborn_snake_01` | Along the Old Road | Orange Among the Ruins | `affaa0767b0d44e3b06a0cbbc012a0a7` | `c56443e8f5e84852bf709b1243f2c29d` |

## Reproducible audit sample

The audit CSV contains 40 unique narrative pairs. It uses proportional scenario strata and deterministic SHA-256 ranking with fixed salt `20260820`. Selection did not use similarity scores or score bands.

The 40 rows are a qualitative inspection set, **not** human validation. All 288 pairs are used for the numerical analysis. Pair scores are not statistically independent because one narrative participates in multiple pairs; the report therefore presents descriptive statistics only.

# Semantic Similarity Analysis (72 generations)

## Dataset and model

- Frozen physical-line prefix: 216
- Input prefix SHA-256 verified: true
- Generation records: 72
- Within-scenario narrative pairs: 288
- Field comparisons: 576
- Unique embedded field texts: 144
- Model: `sentence-transformers/all-mpnet-base-v2`
- Model revision: `e8c3b32edf5434bc2275fc9bab85f82640a19130`
- Embedding dimension: 768
- Device/dtype: `cpu` / `float32`
- Maximum model sequence: 384 wordpieces
- Maximum observed sequence: 51 wordpieces
- Texts that would be truncated: 0

## Method

Original `introduction` and `completionText` are kept separate. Semantic preprocessing only collapses whitespace; case, punctuation, stopwords, and word forms are preserved. Each text is encoded once as an L2-normalized float32 sentence vector. Cosine similarity is the dot product of the two normalized vectors and ranges from -1 to 1; it is not a probability or a percentage.

No semantic high/review cutoff is assigned. The tables are descriptive, and overall statistics are pooled pair-weighted. The macro mean gives each of the 8 scenarios equal weight as a sensitivity result.

## Overall within-scenario results

| Field | Pairs | Pair-weighted mean | Macro mean of scenarios | Median | P90 | Minimum | Maximum |
|---|---:|---:|---:|---:|---:|---:|---:|
| `introduction` | 288 | 0.7476 | 0.7476 | 0.7581 | 0.8662 | 0.4053 | 0.9454 |
| `completionText` | 288 | 0.7300 | 0.7300 | 0.7509 | 0.8440 | 0.3827 | 0.9502 |

## Per-scenario results

| Scenario | Field | Pairs | Mean | Median | P90 | Maximum |
|---|---|---:|---:|---:|---:|---:|
| `collect_mushroom_01` | `introduction` | 36 | 0.7777 | 0.7898 | 0.8965 | 0.9454 |
| `collect_mushroom_01` | `completionText` | 36 | 0.6444 | 0.6645 | 0.7854 | 0.8713 |
| `kill_torch_01` | `introduction` | 36 | 0.7931 | 0.7958 | 0.8552 | 0.9407 |
| `kill_torch_01` | `completionText` | 36 | 0.7759 | 0.7681 | 0.8730 | 0.8809 |
| `slay_caveborn_bear_01` | `introduction` | 36 | 0.7238 | 0.8064 | 0.8638 | 0.9174 |
| `slay_caveborn_bear_01` | `completionText` | 36 | 0.7843 | 0.7886 | 0.8458 | 0.8586 |
| `slay_caveborn_lizard_01` | `introduction` | 36 | 0.7021 | 0.6883 | 0.8549 | 0.9271 |
| `slay_caveborn_lizard_01` | `completionText` | 36 | 0.7363 | 0.7268 | 0.8317 | 0.8713 |
| `slay_caveborn_snake_01` | `introduction` | 36 | 0.7546 | 0.7555 | 0.8398 | 0.9031 |
| `slay_caveborn_snake_01` | `completionText` | 36 | 0.6605 | 0.6622 | 0.7892 | 0.8502 |
| `slay_caveborn_spider_01` | `introduction` | 36 | 0.7391 | 0.7173 | 0.8836 | 0.9345 |
| `slay_caveborn_spider_01` | `completionText` | 36 | 0.7325 | 0.7491 | 0.8311 | 0.9502 |
| `slay_caveborn_turtle_01` | `introduction` | 36 | 0.7288 | 0.7220 | 0.8525 | 0.9282 |
| `slay_caveborn_turtle_01` | `completionText` | 36 | 0.7483 | 0.7666 | 0.8233 | 0.9169 |
| `slay_torch_boss_01` | `introduction` | 36 | 0.7614 | 0.7581 | 0.8400 | 0.8667 |
| `slay_torch_boss_01` | `completionText` | 36 | 0.7575 | 0.7634 | 0.8670 | 0.9387 |

## Relationship with lexical metrics

Spearman is primary because the bounded scores need not be linearly related and Word 3-gram has many ties at zero. Pearson is supplementary. No p-values are reported because pair observations reuse narratives and are not independent. These are pooled descriptive correlations, so they may also include differences among scenarios.

| Field | Lexical metric | Pairs | Spearman rho | Pearson r |
|---|---|---:|---:|---:|
| `introduction` | `tokenLcsF1` | 288 | 0.5694 | 0.5706 |
| `introduction` | `word3gramJaccard` | 288 | 0.3913 | 0.4148 |
| `introduction` | `word1gramJaccard` | 288 | 0.6063 | 0.6147 |
| `completionText` | `tokenLcsF1` | 288 | 0.6335 | 0.6664 |
| `completionText` | `word3gramJaccard` | 288 | 0.5173 | 0.4630 |
| `completionText` | `word1gramJaccard` | 288 | 0.5978 | 0.6044 |

## Highest semantic-cosine pairs

| Field | Rank | Cosine | LCS F1 | Scenario | Title A | Title B | Request A | Request B |
|---|---:|---:|---:|---|---|---|---|---|
| `introduction` | 1 | 0.9454 | 0.5185 | `collect_mushroom_01` | Spores Among the Ruins | Glow Beneath the Ruins | `6ff52e13a61e4d3b947205255688a049` | `ff1ce9ba9c094e11b26db5d3e4bfc790` |
| `introduction` | 2 | 0.9407 | 0.6866 | `kill_torch_01` | Torches in the Open Air | Lights in the Ruins | `6726c5f7d00e40edb749fc0be022ab2d` | `c84b1ba69ae446619a41055a692f39fb` |
| `introduction` | 3 | 0.9345 | 0.3662 | `slay_caveborn_spider_01` | Eyes Beneath the Western Rocks | Eyes Beneath the Ruins | `412795ab50ee4e71902a13829f496ba9` | `d2984f8b3f1e43bfa1e91dbe671d2c4e` |
| `introduction` | 4 | 0.9282 | 0.5797 | `slay_caveborn_turtle_01` | The Spiralback of the Western Rocks | The Spiralstone Sentinel | `265d9ac072544b57b4832f470a9101ee` | `cd7bfeca2db94c58b6bbafa51de3946c` |
| `introduction` | 5 | 0.9271 | 0.6885 | `slay_caveborn_lizard_01` | Crests Beneath the Ruins | Crests Beneath the Ruins | `2ff34069fd8b447bbe1ecd41c4398f3d` | `aec11dd626ac49e1912e756b2474941d` |
| `completionText` | 1 | 0.9502 | 0.8235 | `slay_caveborn_spider_01` | Eyes Beneath the Fallen Road | Eyes Beneath the Ruins | `404a2119c3764cffa42500f36124f347` | `eb0fef25caa74ea88bc0fdf341786eb2` |
| `completionText` | 2 | 0.9387 | 0.6441 | `slay_torch_boss_01` | The Last Flame of the Arena | The Last Flame in the Arena | `823b828a2e1c460098b7eaf6e69a127a` | `c261543583ee402287f2d1cf96783789` |
| `completionText` | 3 | 0.9169 | 0.5098 | `slay_caveborn_turtle_01` | The Stone-Shell Wanderer | The Spiralstone Sentinel | `9d95fd68135c45ce808847a8df993663` | `cd7bfeca2db94c58b6bbafa51de3946c` |
| `completionText` | 4 | 0.9073 | 0.5600 | `slay_torch_boss_01` | The Last Flame of the Arena | The Last Flame of the Arena | `01e97041599f4b1bb5434995c4f3fd90` | `d551fd878ca046a2ada939f6fab368c2` |
| `completionText` | 5 | 0.9041 | 0.6786 | `slay_caveborn_spider_01` | Eyes Beneath the Western Rocks | Eyes Beneath the Ruins | `e48a6de0ca804ad1a24207b399476991` | `eb0fef25caa74ea88bc0fdf341786eb2` |

## Audit and interpretation limits

The existing 40 hash-ranked audit pairs are preserved in their original order and enriched with both field-level semantic scores. They were not resampled using semantic results.

Same-scenario texts necessarily share enemies, places, objectives, and events. A high cosine can therefore reflect correct scenario adherence, not merely poor creativity. Completion texts are shorter and more functionally constrained than introductions. Sentence embeddings also compress a whole passage into one vector and cannot locate copied wording; interpret them beside Token LCS F1, Word 3-gram Jaccard, and the original texts. No two scores are averaged into a single quality score.

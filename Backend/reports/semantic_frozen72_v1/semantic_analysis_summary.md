# Semantic Similarity Analysis (72 generations)

## Dataset and model

- Frozen physical-line prefix: 206
- Input prefix SHA-256 verified: true
- Generation records: 72
- Within-scenario narrative pairs: 296
- Field comparisons: 592
- Unique embedded field texts: 144
- Model: `sentence-transformers/all-mpnet-base-v2`
- Model revision: `e8c3b32edf5434bc2275fc9bab85f82640a19130`
- Embedding dimension: 768
- Device/dtype: `cpu` / `float32`
- Maximum model sequence: 384 wordpieces
- Maximum observed sequence: 59 wordpieces
- Texts that would be truncated: 0

## Method

Original `introduction` and `completionText` are kept separate. Semantic preprocessing only collapses whitespace; case, punctuation, stopwords, and word forms are preserved. Each text is encoded once as an L2-normalized float32 sentence vector. Cosine similarity is the dot product of the two normalized vectors and ranges from -1 to 1; it is not a probability or a percentage.

No semantic high/review cutoff is assigned. The tables are descriptive, and overall statistics are pooled pair-weighted. The macro mean gives each of the 8 scenarios equal weight as a sensitivity result.

## Overall within-scenario results

| Field | Pairs | Pair-weighted mean | Macro mean of scenarios | Median | P90 | Minimum | Maximum |
|---|---:|---:|---:|---:|---:|---:|---:|
| `introduction` | 296 | 0.8059 | 0.8020 | 0.8137 | 0.8769 | 0.5764 | 0.9288 |
| `completionText` | 296 | 0.6534 | 0.6527 | 0.6668 | 0.7998 | 0.2524 | 0.9297 |

## Per-scenario results

| Scenario | Field | Pairs | Mean | Median | P90 | Maximum |
|---|---|---:|---:|---:|---:|---:|
| `collect_mushroom_01` | `introduction` | 28 | 0.8059 | 0.8149 | 0.8678 | 0.9096 |
| `collect_mushroom_01` | `completionText` | 28 | 0.6448 | 0.7106 | 0.8434 | 0.9297 |
| `kill_torch_01` | `introduction` | 36 | 0.8060 | 0.8061 | 0.8662 | 0.8833 |
| `kill_torch_01` | `completionText` | 36 | 0.6463 | 0.6365 | 0.8228 | 0.8554 |
| `slay_caveborn_bear_01` | `introduction` | 45 | 0.8340 | 0.8349 | 0.8751 | 0.9104 |
| `slay_caveborn_bear_01` | `completionText` | 45 | 0.7045 | 0.7082 | 0.8249 | 0.8777 |
| `slay_caveborn_lizard_01` | `introduction` | 45 | 0.7937 | 0.7877 | 0.8520 | 0.9288 |
| `slay_caveborn_lizard_01` | `completionText` | 45 | 0.6283 | 0.6118 | 0.7647 | 0.9270 |
| `slay_caveborn_snake_01` | `introduction` | 45 | 0.8085 | 0.8099 | 0.8644 | 0.8948 |
| `slay_caveborn_snake_01` | `completionText` | 45 | 0.6404 | 0.6383 | 0.7424 | 0.8199 |
| `slay_caveborn_spider_01` | `introduction` | 21 | 0.8505 | 0.8561 | 0.8867 | 0.9050 |
| `slay_caveborn_spider_01` | `completionText` | 21 | 0.6026 | 0.5941 | 0.7100 | 0.7618 |
| `slay_caveborn_turtle_01` | `introduction` | 55 | 0.8116 | 0.8315 | 0.8864 | 0.9068 |
| `slay_caveborn_turtle_01` | `completionText` | 55 | 0.6529 | 0.6832 | 0.8055 | 0.8758 |
| `slay_torch_boss_01` | `introduction` | 21 | 0.7059 | 0.7137 | 0.7743 | 0.7914 |
| `slay_torch_boss_01` | `completionText` | 21 | 0.7016 | 0.6958 | 0.7871 | 0.8886 |

## Relationship with lexical metrics

Spearman is primary because the bounded scores need not be linearly related and Word 3-gram has many ties at zero. Pearson is supplementary. No p-values are reported because pair observations reuse narratives and are not independent. These are pooled descriptive correlations, so they may also include differences among scenarios.

| Field | Lexical metric | Pairs | Spearman rho | Pearson r |
|---|---|---:|---:|---:|
| `introduction` | `tokenLcsF1` | 296 | 0.4556 | 0.4510 |
| `introduction` | `word3gramJaccard` | 296 | 0.4496 | 0.3920 |
| `introduction` | `word1gramJaccard` | 296 | 0.5525 | 0.5265 |
| `completionText` | `tokenLcsF1` | 296 | 0.6035 | 0.6017 |
| `completionText` | `word3gramJaccard` | 296 | 0.5150 | 0.5143 |
| `completionText` | `word1gramJaccard` | 296 | 0.5947 | 0.6000 |

## Highest semantic-cosine pairs

| Field | Rank | Cosine | LCS F1 | Scenario | Title A | Title B | Request A | Request B |
|---|---:|---:|---:|---|---|---|---|---|
| `introduction` | 1 | 0.9288 | 0.3409 | `slay_caveborn_lizard_01` | Crestrunners of the Western Rocks | Crests Among the Ruins | `f389ec3951d94467806e46bb9d5d20a4` | `ff569c416ae04b82a9be4138ac9d3f34` |
| `introduction` | 2 | 0.9104 | 0.4789 | `slay_caveborn_bear_01` | Claws on the Old Road | Claws in the Ruins | `d84458be95224fcda2a6c32ab2697695` | `e82f128a419d4be3b85fe145aa5ef3d5` |
| `introduction` | 3 | 0.9096 | 0.4333 | `collect_mushroom_01` | Spores Among the Stones | Spores in the Silent Ring | `2645ecf9589a4a9e8e706767e276a76f` | `c3559d405854453999c14c459c7fee47` |
| `introduction` | 4 | 0.9068 | 0.3077 | `slay_caveborn_turtle_01` | The Spiral Shell | The Western Spiralback | `630250d3a38e48f581f253ea12827f20` | `8bce7ca488fe46e686933d36c423a242` |
| `introduction` | 5 | 0.9062 | 0.5846 | `slay_caveborn_turtle_01` | The Spiral in Stone | The Spiral in the Stone | `477031fdb9304e4f965335391bc21f06` | `cc4db7a70efe4f589947c86a56fc990f` |
| `completionText` | 1 | 0.9297 | 0.5000 | `collect_mushroom_01` | Spores Among the Stones | Spores in the Silent Ring | `2645ecf9589a4a9e8e706767e276a76f` | `c3559d405854453999c14c459c7fee47` |
| `completionText` | 2 | 0.9270 | 0.8824 | `slay_caveborn_lizard_01` | Cre，sts by the Old Road | Crests Among the Ruins | `38049414cb684cfdb76cf1ea484f7bcb` | `7d091825d2a54b52aca66e0029009c47` |
| `completionText` | 3 | 0.8886 | 0.4103 | `slay_torch_boss_01` | The Last Light in the Arena | The Last Flame of the Arena | `726d411d1fe74c569d0047afbbf0e7ea` | `aa66f3792e3a4a27b0219a0fc1e244d1` |
| `completionText` | 4 | 0.8777 | 0.6857 | `slay_caveborn_bear_01` | Claws by the Western Rocks | Claws Among the Ruins | `6db97ea99d5d42ada490241797be9d62` | `cda61949cac4437d88ecaad238601b9d` |
| `completionText` | 5 | 0.8768 | 0.6250 | `slay_caveborn_lizard_01` | Cre，sts by the Old Road | Cre rests Among the Ruins | `38049414cb684cfdb76cf1ea484f7bcb` | `39d6a848b4b64697a5abb4928193eee3` |

## Audit and interpretation limits

The existing 40 hash-ranked audit pairs are preserved in their original order and enriched with both field-level semantic scores. They were not resampled using semantic results.

Same-scenario texts necessarily share enemies, places, objectives, and events. A high cosine can therefore reflect correct scenario adherence, not merely poor creativity. Completion texts are shorter and more functionally constrained than introductions. Sentence embeddings also compress a whole passage into one vector and cannot locate copied wording; interpret them beside Token LCS F1, Word 3-gram Jaccard, and the original texts. No two scores are averaged into a single quality score.

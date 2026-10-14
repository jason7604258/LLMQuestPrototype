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
- Maximum observed sequence: 65 wordpieces
- Texts that would be truncated: 0

## Method

Original `introduction` and `completionText` are kept separate. Semantic preprocessing only collapses whitespace; case, punctuation, stopwords, and word forms are preserved. Each text is encoded once as an L2-normalized float32 sentence vector. Cosine similarity is the dot product of the two normalized vectors and ranges from -1 to 1; it is not a probability or a percentage.

No semantic high/review cutoff is assigned. The tables are descriptive, and overall statistics are pooled pair-weighted. The macro mean gives each of the 8 scenarios equal weight as a sensitivity result.

## Overall within-scenario results

| Field | Pairs | Pair-weighted mean | Macro mean of scenarios | Median | P90 | Minimum | Maximum |
|---|---:|---:|---:|---:|---:|---:|---:|
| `introduction` | 288 | 0.8120 | 0.8120 | 0.8128 | 0.8886 | 0.6666 | 0.9461 |
| `completionText` | 288 | 0.7477 | 0.7477 | 0.7642 | 0.8736 | 0.4224 | 0.9545 |

## Per-scenario results

| Scenario | Field | Pairs | Mean | Median | P90 | Maximum |
|---|---|---:|---:|---:|---:|---:|
| `collect_mushroom_01` | `introduction` | 36 | 0.7951 | 0.7884 | 0.8717 | 0.9378 |
| `collect_mushroom_01` | `completionText` | 36 | 0.6763 | 0.6655 | 0.8640 | 0.9267 |
| `kill_torch_01` | `introduction` | 36 | 0.7975 | 0.7874 | 0.8906 | 0.9194 |
| `kill_torch_01` | `completionText` | 36 | 0.6071 | 0.6140 | 0.7085 | 0.7837 |
| `slay_caveborn_bear_01` | `introduction` | 36 | 0.8329 | 0.8240 | 0.9082 | 0.9171 |
| `slay_caveborn_bear_01` | `completionText` | 36 | 0.8399 | 0.8458 | 0.8930 | 0.9545 |
| `slay_caveborn_lizard_01` | `introduction` | 36 | 0.8286 | 0.8358 | 0.8853 | 0.9131 |
| `slay_caveborn_lizard_01` | `completionText` | 36 | 0.6978 | 0.6823 | 0.7882 | 0.9273 |
| `slay_caveborn_snake_01` | `introduction` | 36 | 0.8005 | 0.8027 | 0.8696 | 0.9157 |
| `slay_caveborn_snake_01` | `completionText` | 36 | 0.8445 | 0.8459 | 0.8940 | 0.9275 |
| `slay_caveborn_spider_01` | `introduction` | 36 | 0.8286 | 0.8299 | 0.8832 | 0.9461 |
| `slay_caveborn_spider_01` | `completionText` | 36 | 0.8086 | 0.8115 | 0.8723 | 0.9147 |
| `slay_caveborn_turtle_01` | `introduction` | 36 | 0.8323 | 0.8394 | 0.8961 | 0.9235 |
| `slay_caveborn_turtle_01` | `completionText` | 36 | 0.7777 | 0.7634 | 0.8538 | 0.9005 |
| `slay_torch_boss_01` | `introduction` | 36 | 0.7802 | 0.7783 | 0.8466 | 0.8862 |
| `slay_torch_boss_01` | `completionText` | 36 | 0.7301 | 0.7426 | 0.8396 | 0.8930 |

## Relationship with lexical metrics

Spearman is primary because the bounded scores need not be linearly related and Word 3-gram has many ties at zero. Pearson is supplementary. No p-values are reported because pair observations reuse narratives and are not independent. These are pooled descriptive correlations, so they may also include differences among scenarios.

| Field | Lexical metric | Pairs | Spearman rho | Pearson r |
|---|---|---:|---:|---:|
| `introduction` | `tokenLcsF1` | 288 | 0.4417 | 0.4615 |
| `introduction` | `word3gramJaccard` | 288 | 0.3907 | 0.3860 |
| `introduction` | `word1gramJaccard` | 288 | 0.5083 | 0.5196 |
| `completionText` | `tokenLcsF1` | 288 | 0.6748 | 0.6483 |
| `completionText` | `word3gramJaccard` | 288 | 0.6545 | 0.5467 |
| `completionText` | `word1gramJaccard` | 288 | 0.7299 | 0.6814 |

## Highest semantic-cosine pairs

| Field | Rank | Cosine | LCS F1 | Scenario | Title A | Title B | Request A | Request B |
|---|---:|---:|---:|---|---|---|---|---|
| `introduction` | 1 | 0.9461 | 0.6304 | `slay_caveborn_spider_01` | Yellow Eyes Among the Ruins | Along the Forgotten Road | `73185b4e3247444c82f6593bb261f71f` | `9804422119b742c88c392c84568d766c` |
| `introduction` | 2 | 0.9378 | 0.7711 | `collect_mushroom_01` | A Quiet Kind of Light | A Quiet Return | `355b28e559e04e45a231dde736928994` | `36150134a70e4174a53840ab32aa88a6` |
| `introduction` | 3 | 0.9235 | 0.4634 | `slay_caveborn_turtle_01` | A Spiral Among the Ruins | Spirals of Forgotten Stone | `04f74ff206e741a696d1c333e2767495` | `23897e25c73a44cfb1ae8fa16667d359` |
| `introduction` | 4 | 0.9194 | 0.5294 | `kill_torch_01` | Flames Among the Grass | Room for the Wind | `9a2099d6327b41f4b93b21307841ac5d` | `adb5eb127226484e930b5ced2c8abacf` |
| `introduction` | 5 | 0.9188 | 0.4167 | `collect_mushroom_01` | A Glow in the Grass | A Quiet Return | `39da90f2360e42cc8adc3262777c8a37` | `cdae7807eae74ec8be24a2b341f69187` |
| `completionText` | 1 | 0.9545 | 0.6061 | `slay_caveborn_bear_01` | Claws Among the Ruins | Claws Among the Ruins | `173a4cf0df3940308a7b0dfcfb5af031` | `557b1b3ab3eb4bc7a2a39b978af066bd` |
| `completionText` | 2 | 0.9275 | 0.6800 | `slay_caveborn_snake_01` | Bright Bands in the Ruins | Orange Among the Green | `09b2d175be144123b62de89e9be75f82` | `2c8b2d4a377c4e36afd9d15c72393092` |
| `completionText` | 3 | 0.9273 | 0.3636 | `slay_caveborn_lizard_01` | Yellow Crests on the Old Road | Yellow Crests on the Old Road | `2da5a8ee2d11492b9ea71f7ab09111a9` | `64c76cd6cf70458a9a015b97ca4aaafa` |
| `completionText` | 4 | 0.9267 | 0.3902 | `collect_mushroom_01` | A Quiet Kind of Light | A Quiet Return | `4b3d503304a4449eb2ba12754a06d137` | `cdae7807eae74ec8be24a2b341f69187` |
| `completionText` | 5 | 0.9237 | 0.6269 | `slay_caveborn_snake_01` | Orange Bands on the Old Road | Orange Among the Ruins | `c0887b7b91714b6eb7d4c962a0a9892c` | `c56443e8f5e84852bf709b1243f2c29d` |

## Audit and interpretation limits

The existing 40 hash-ranked audit pairs are preserved in their original order and enriched with both field-level semantic scores. They were not resampled using semantic results.

Same-scenario texts necessarily share enemies, places, objectives, and events. A high cosine can therefore reflect correct scenario adherence, not merely poor creativity. Completion texts are shorter and more functionally constrained than introductions. Sentence embeddings also compress a whole passage into one vector and cannot locate copied wording; interpret them beside Token LCS F1, Word 3-gram Jaccard, and the original texts. No two scores are averaged into a single quality score.

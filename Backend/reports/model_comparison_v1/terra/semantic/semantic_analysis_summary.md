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
- Maximum observed sequence: 55 wordpieces
- Texts that would be truncated: 0

## Method

Original `introduction` and `completionText` are kept separate. Semantic preprocessing only collapses whitespace; case, punctuation, stopwords, and word forms are preserved. Each text is encoded once as an L2-normalized float32 sentence vector. Cosine similarity is the dot product of the two normalized vectors and ranges from -1 to 1; it is not a probability or a percentage.

No semantic high/review cutoff is assigned. The tables are descriptive, and overall statistics are pooled pair-weighted. The macro mean gives each of the 8 scenarios equal weight as a sensitivity result.

## Overall within-scenario results

| Field | Pairs | Pair-weighted mean | Macro mean of scenarios | Median | P90 | Minimum | Maximum |
|---|---:|---:|---:|---:|---:|---:|---:|
| `introduction` | 288 | 0.7371 | 0.7371 | 0.7499 | 0.8646 | 0.4466 | 0.9181 |
| `completionText` | 288 | 0.6544 | 0.6544 | 0.6665 | 0.8007 | 0.3171 | 0.9064 |

## Per-scenario results

| Scenario | Field | Pairs | Mean | Median | P90 | Maximum |
|---|---|---:|---:|---:|---:|---:|
| `collect_mushroom_01` | `introduction` | 36 | 0.7724 | 0.7857 | 0.8651 | 0.9181 |
| `collect_mushroom_01` | `completionText` | 36 | 0.6630 | 0.6656 | 0.7870 | 0.8934 |
| `kill_torch_01` | `introduction` | 36 | 0.7631 | 0.7563 | 0.8533 | 0.8953 |
| `kill_torch_01` | `completionText` | 36 | 0.7586 | 0.7600 | 0.8396 | 0.8999 |
| `slay_caveborn_bear_01` | `introduction` | 36 | 0.7177 | 0.7294 | 0.8386 | 0.8656 |
| `slay_caveborn_bear_01` | `completionText` | 36 | 0.6739 | 0.6727 | 0.7964 | 0.8620 |
| `slay_caveborn_lizard_01` | `introduction` | 36 | 0.6875 | 0.6852 | 0.8197 | 0.8963 |
| `slay_caveborn_lizard_01` | `completionText` | 36 | 0.5413 | 0.5212 | 0.6923 | 0.8851 |
| `slay_caveborn_snake_01` | `introduction` | 36 | 0.7738 | 0.8286 | 0.8853 | 0.9019 |
| `slay_caveborn_snake_01` | `completionText` | 36 | 0.6026 | 0.5937 | 0.7026 | 0.8854 |
| `slay_caveborn_spider_01` | `introduction` | 36 | 0.6615 | 0.6477 | 0.7892 | 0.8390 |
| `slay_caveborn_spider_01` | `completionText` | 36 | 0.6220 | 0.6533 | 0.7198 | 0.8192 |
| `slay_caveborn_turtle_01` | `introduction` | 36 | 0.7299 | 0.7942 | 0.8753 | 0.9129 |
| `slay_caveborn_turtle_01` | `completionText` | 36 | 0.6235 | 0.6340 | 0.7301 | 0.8083 |
| `slay_torch_boss_01` | `introduction` | 36 | 0.7908 | 0.7927 | 0.8361 | 0.8589 |
| `slay_torch_boss_01` | `completionText` | 36 | 0.7505 | 0.7472 | 0.8106 | 0.9064 |

## Relationship with lexical metrics

Spearman is primary because the bounded scores need not be linearly related and Word 3-gram has many ties at zero. Pearson is supplementary. No p-values are reported because pair observations reuse narratives and are not independent. These are pooled descriptive correlations, so they may also include differences among scenarios.

| Field | Lexical metric | Pairs | Spearman rho | Pearson r |
|---|---|---:|---:|---:|
| `introduction` | `tokenLcsF1` | 288 | 0.5796 | 0.5724 |
| `introduction` | `word3gramJaccard` | 288 | 0.2751 | 0.2977 |
| `introduction` | `word1gramJaccard` | 288 | 0.6307 | 0.6132 |
| `completionText` | `tokenLcsF1` | 288 | 0.5974 | 0.6035 |
| `completionText` | `word3gramJaccard` | 288 | 0.4369 | 0.4300 |
| `completionText` | `word1gramJaccard` | 288 | 0.6290 | 0.6383 |

## Highest semantic-cosine pairs

| Field | Rank | Cosine | LCS F1 | Scenario | Title A | Title B | Request A | Request B |
|---|---:|---:|---:|---|---|---|---|---|
| `introduction` | 1 | 0.9181 | 0.4407 | `collect_mushroom_01` | Spores in the Ruins | Glowcap Gathering | `b4fc196c68da484daa08dd1074d7895e` | `ef4a803591634ef09867b7a8175eaeb7` |
| `introduction` | 2 | 0.9129 | 0.3158 | `slay_caveborn_turtle_01` | The Spiral Shell | The Stone-Shelled Wanderer | `e3208bb3bc6c4509a3f71769dd06298c` | `ed2b10cb96d54bd3a6886fb9e10e214f` |
| `introduction` | 3 | 0.9036 | 0.4923 | `slay_caveborn_turtle_01` | The Stone-Shelled Wanderer | The Spiral Shell | `021fc7e35a6a44e69a0f5847a6916ba7` | `e3208bb3bc6c4509a3f71769dd06298c` |
| `introduction` | 4 | 0.9019 | 0.4407 | `slay_caveborn_snake_01` | Fangs in the Western Cave | The Western Hollow | `01e3d7dc0721429398ee00e28cff7cd4` | `2c97f044cc964456bbde4901548559b0` |
| `introduction` | 5 | 0.8982 | 0.4068 | `slay_caveborn_snake_01` | Echoes in the Western Cave | Bands in the Shadows | `900b74340c3d4ef8a6a5719574afa3b5` | `b8d91a76cc8a455393c914b7e60d1c86` |
| `completionText` | 1 | 0.9064 | 0.7000 | `slay_torch_boss_01` | The Last Arena Flame | The Arena’s Last Flame | `0e83cd86e85444dc875a4ed3a4fd24b8` | `75d27ce875e5482fb8f9324accd50ac5` |
| `completionText` | 2 | 0.8999 | 0.6875 | `kill_torch_01` | Lights in the Mountain Arena | Embers in the Open Arena | `512b469e47ec46d193da3101b7b81e80` | `c379082ef386419a89c75b7c53d9960d` |
| `completionText` | 3 | 0.8934 | 0.4571 | `collect_mushroom_01` | Spores Among the Stones | Spores Among the Stones | `5b90227eafd44b218bcc8500c2b026ed` | `9f98fa773faf466faa4699351120cc1f` |
| `completionText` | 4 | 0.8886 | 0.5517 | `slay_torch_boss_01` | The Last Arena Flame | The Last Arena Flame | `7aa01972e0cf472992f01b933552109f` | `c94e6867c42047189a573ebb56ed05f5` |
| `completionText` | 5 | 0.8876 | 0.6207 | `slay_torch_boss_01` | The Arena’s Last Flame | The Last Arena Flame | `59031cd139f046859c88194cfadcf4df` | `c94e6867c42047189a573ebb56ed05f5` |

## Audit and interpretation limits

The existing 40 hash-ranked audit pairs are preserved in their original order and enriched with both field-level semantic scores. They were not resampled using semantic results.

Same-scenario texts necessarily share enemies, places, objectives, and events. A high cosine can therefore reflect correct scenario adherence, not merely poor creativity. Completion texts are shorter and more functionally constrained than introductions. Sentence embeddings also compress a whole passage into one vector and cannot locate copied wording; interpret them beside Token LCS F1, Word 3-gram Jaccard, and the original texts. No two scores are averaged into a single quality score.

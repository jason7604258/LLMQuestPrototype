# LLM Narrative Experiment Summary

Source: `<PROJECT_ROOT>/Backend/logs/demo_narrative_runs_2026-08-20_take01.jsonl`

## Dataset

- Valid records: 206
- Malformed lines skipped: 0
- Generation records: 72
- Gameplay events: 134
- Period (UTC): 2026-08-20T17:57:23.913743+00:00 to 2026-08-20T21:10:35.730714+00:00

## Generation reliability

- OpenAI attempts: 72
- OpenAI narratives returned: 72
- OpenAI attempt success rate: 100.0%
- Fallback narratives: 0
- Fallback rate: 0.0%
- Backend acceptance rate (known schema-2 rows): 100.0%
- Unity acceptance rate (recorded starts): 100.0%

## Performance and cost

- Average OpenAI latency: 8.777 s
- Average backend latency: 8.822 s
- Total input tokens: 53127
- Total output tokens: 26967
- Total tokens: 80094
- Average tokens per measured generation: 1112.4
- Estimated total cost: $1.074645
- Average estimated cost: $0.014926

## Gameplay

- Scenarios started: 72
- Scenarios completed: 62
- Completion rate: 86.1%
- Started but not completed: 10
- Average completion time: 28.475 s

## Narrative repetition (lexical baseline)

- Method: Normalized lexical similarity across title, introduction, and completionText
- High-similarity threshold: 85%
- Exact creative-text pairs: 0
- High-similarity non-exact pairs: 0
- Repeated normalized title groups: 15

> This is a wording-based baseline, not a semantic or human quality score. The mechanically repetitive objective is excluded from the comparison.

## Objective target-name variation (player-facing UI)

- Method: For each generation, the UI uses `targetDisplayNameSingular` when the required amount is 1 and `targetDisplayNamePlural` otherwise. Unity constructs the objective instruction from the fixed scenario verb, required amount, and selected name; progress is displayed separately.
- Target-name selections: 72
- Distinct UI target names: 44
- Reused selections: 28
- Unique-name rate: 61.1%
- Reuse rate: 38.9%
- Cross-target name collisions: 0 (no two different enemy or item types used exactly the same UI target name)

Example objective and progress presentation:

- Amount 1: `Defeat 1 Spiral-Shell Cave Turtle.` with `0 / 1`
- Amount 2: `Defeat 2 Many-Eyed Cave Spiders.` with `0 / 2`
- Amount 3: `Collect 3 Pale-Cap Mushrooms.` with `0 / 3`

The eleven turtle scenarios used five different player-facing names. `Spiral-Shell Cave Turtle` was reused seven times; each of the other names appeared once.

| Turtle UI target name | Occurrences |
|---|---:|
| Spiral-Shell Cave Turtle | 7 |
| Spiral-Shelled Cave Turtle | 1 |
| Spiralback Cave Turtle | 1 |
| Caveborn Spiralback | 1 |
| Weathered Spiralback | 1 |

The eight mushroom scenarios used six different player-facing names. `Pale-Cap Mushrooms` was reused three times; each of the other names appeared once.

| Mushroom UI target name | Occurrences |
|---|---:|
| Pale-Cap Mushrooms | 3 |
| Pale Sporecaps | 1 |
| Paleglow Mushrooms | 1 |
| Sporelight Mushrooms | 1 |
| Pale-Spored Mushrooms | 1 |
| Pale Glowcaps | 1 |

These results demonstrate that one underlying target type can receive multiple UI names. The system requests variation, but it does not guarantee a previously unseen name for every generation.

## By scenario

| Scenario | Type | Generated | OpenAI | Fallback | Started | Completed | Completion rate | Avg. completion (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| collect_mushroom_01 | CollectItems | 8 | 8 | 0 | 8 | 7 | 87.5% | 14.659 |
| kill_torch_01 | KillEnemies | 9 | 9 | 0 | 9 | 8 | 88.9% | 32.047 |
| slay_caveborn_bear_01 | KillEnemies | 10 | 10 | 0 | 10 | 9 | 90.0% | 21.915 |
| slay_caveborn_lizard_01 | KillEnemies | 10 | 10 | 0 | 10 | 8 | 80.0% | 37.400 |
| slay_caveborn_snake_01 | KillEnemies | 10 | 10 | 0 | 10 | 9 | 90.0% | 25.018 |
| slay_caveborn_spider_01 | KillEnemies | 7 | 7 | 0 | 7 | 6 | 85.7% | 44.555 |
| slay_caveborn_turtle_01 | KillEnemies | 11 | 11 | 0 | 11 | 8 | 72.7% | 32.455 |
| slay_torch_boss_01 | SlayBoss | 7 | 7 | 0 | 7 | 7 | 100.0% | 22.552 |

## Similar narrative pairs

No exact or above-threshold pairs were found.

## Repeated titles

| Title | Occurrences | Scenario IDs |
|---|---:|---|
| Bands in the Dark | 2 | slay_caveborn_snake_01 |
| Claws Among the Ruins | 3 | slay_caveborn_bear_01 |
| Claws in the Western Rocks | 2 | slay_caveborn_bear_01 |
| Claws on the Old Road | 2 | slay_caveborn_bear_01 |
| Crests Among the Ruins | 3 | slay_caveborn_lizard_01 |
| Embers in the Mountain Arena | 2 | kill_torch_01 |
| Eyes Along the Old Road | 3 | slay_caveborn_spider_01 |
| Eyes in the Western Rocks | 3 | slay_caveborn_spider_01 |
| Flames in the Empty Arena | 2 | kill_torch_01 |
| Glow Among the Ruins | 3 | collect_mushroom_01 |
| Spores Among the Stones | 4 | collect_mushroom_01 |
| The Arena’s Last Flame | 2 | slay_torch_boss_01 |
| The Last Flame of the Arena | 3 | slay_torch_boss_01 |
| The Spiral in the Stone | 2 | slay_caveborn_turtle_01 |
| The Spiral Shell | 6 | slay_caveborn_turtle_01 |

# Step 16 — Unity-Controlled Random Scenarios

## Goal

Unity randomly chooses one of the authored and balanced scenario definitions.
Only after that choice does the backend ask the LLM to create a narrative that
fits the fixed gameplay facts.

## Runtime order

1. The player presses `START SCENARIO` or `NEXT SCENARIO`.
2. `QuestManager` filters invalid entries from `availableScenarios`.
3. Unity shuffles all unique valid scenarios into a fair cycle. Each scenario
   is selected exactly once before the cycle is refilled and reshuffled.
   With more than one option, the first scenario of a new cycle also differs
   from the final scenario of the previous cycle.
4. Unity sends the selected scenario ID, type, target ID, amount, descriptions,
   tone, and previous story summary to the backend.
5. The backend returns narrative presentation data only.
6. Unity validates the response and reconstructs the selected scenario's fixed
   Arena targets before activating progress tracking.

The LLM does not select the scenario and cannot change target count, target
identity, rewards, health, damage, or map rules.

## Available scenarios

| Scenario | Fixed gameplay targets reconstructed for the run |
| --- | --- |
| `kill_torch_01` | Five non-boss enemies with ID `enemy_torch` |
| `collect_mushroom_01` | Three authored pickups with ID `item_mushroom` |
| `slay_torch_boss_01` | One enemy with boss ID `boss_torch_warden` |

`ScenarioTargetResetter` captures inactive runtime templates from the authored
Arena objects. It resets only the target type needed by the selected scenario.
This lets a player complete multiple scenarios in one Play Mode session without
running out of enemies, mushrooms, or the boss.

Boss templates are excluded from `KillEnemies`, even when a boss shares an
enemy-family ID such as `enemy_torch`. A boss death reports only its boss ID, so
it cannot advance an ordinary-enemy objective.

## Manual acceptance test

1. Enter Play Mode with the local backend running.
2. Press `START SCENARIO` and note the Console line beginning with
   `Randomly selected scenario`.
3. Complete the selected objective.
4. Press `NEXT SCENARIO` without leaving Play Mode.
5. Complete three consecutive runs and confirm the Console shows all three
   scenario IDs exactly once, in any order. The final Console number
   `Fair cycle remaining` should count down from `2` to `0`.
6. Start a fourth run and confirm it begins a newly shuffled cycle without
   repeating the third run's scenario immediately.
7. Confirm a repeated scenario's targets have reappeared in the Arena.
8. Confirm each narrative references the saved previous story while preserving
   the newly selected scenario's fixed amount.

For a focused manual test, disable `Randomize Scenario On Start` on
`QuestManager` and assign the desired `Active Scenario`. Re-enable it after the
test.

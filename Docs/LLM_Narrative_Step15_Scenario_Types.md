# Step 15 — Additional Fixed Scenario Types

## Goal

Support three mechanically fixed scenario types while keeping Unity in control
of gameplay and the LLM limited to narrative presentation.

## Scenario assets

| Asset | Type | Fixed target | Amount |
| --- | --- | --- | --- |
| `KillTorchEnemies` | `KillEnemies` | `enemy_torch` | 5 |
| `CollectMushrooms` | `CollectItems` | `item_mushroom` | 3 |
| `SlayTorchBoss` | `SlayBoss` | `boss_torch_warden` | 1 |

All three assets are listed in `QuestManager.availableScenarios`. Step 16 now
selects from this balanced list. `KillTorchEnemies` remains the serialized
fallback when random selection is disabled for a focused test.

## Gameplay event ownership

- `Enemy_Health.EnemyKilled` reports the fixed normal enemy ID.
- `Inventory_Manager.ItemCollected` reports an item only after the inventory
  successfully accepts an authored world pickup. An item dropped from the
  player's inventory does not report progress, so it cannot be dropped and
  collected repeatedly to complete the scenario.
- `Enemy_Health.BossKilled` reports the fixed boss ID.
- `QuestManager` ignores every event whose type or target ID does not match the
  active `ScenarioDefinition`.

The Arena contains three mushroom pickups. `Enemy_Torch_Boss` is the fixed boss
variant: it retains `enemy_torch` identity for the original kill scenario and
also reports `boss_torch_warden` for the boss scenario. Its fixed values are 8
health and 2 contact damage.

## Narrative safety

The backend and Unity both validate all required narrative fields and require
the objective to contain the exact fixed amount. Unity constructs the displayed
objective from `ScenarioDefinition.requiredAmount` and the validated display
name, so model wording cannot change the real target count.

## Quest UI states

- With no active scenario, the UI is a compact start card positioned below the
  existing top-left level and experience UI.
- Generation, the initial narrative, and completion use the expanded panel in
  the same level-aligned position; it grows downward instead of jumping sides.
- While a scenario is active, `-` collapses it to a compact objective tracker
  and `+` restores the complete story. Both states keep the same top spacing
  below the level display.
- Decorative panel images do not receive raycasts, so they do not block the
  inventory UI underneath; only the actual buttons receive clicks.

## Manual acceptance test before Step 16

For a focused test of one scenario, temporarily disable
`Randomize Scenario On Start` before entering Play Mode.

1. Select `QuestSystem` in the Arena scene.
2. In `QuestManager`, assign the desired asset to `Active Scenario`.
3. Enter Play Mode and start the scenario.
4. For `CollectMushrooms`, collect all three mushroom loot objects and confirm
   progress reaches `3 / 3`.
5. For `SlayTorchBoss`, defeat the enlarged `Enemy_Torch_Boss` and confirm
   progress reaches `1 / 1`.
6. Re-enable `Randomize Scenario On Start` after focused testing.

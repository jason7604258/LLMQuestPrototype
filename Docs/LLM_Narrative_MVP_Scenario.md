# LLM Narrative MVP — Fixed Scenario

## Purpose

This document freezes the gameplay specification for the first LLM narrative
prototype. Unity owns and executes every gameplay rule below. The LLM will only
provide a narrative wrapper in a later step.

## Fixed scenario

| Field | Fixed value |
| --- | --- |
| Scenario ID | `kill_torch_01` |
| Scenario type | `KillEnemies` |
| Internal target ID | `enemy_torch` |
| Required amount | `5` |
| Map ID | `arena` |
| Experience reward | `15` |
| Gold reward | `10` |

## Target facts supplied to the LLM

- Visual description: A humanoid warrior carrying a burning torch.
- Abilities: Chases the player and attacks at close range.
- Restrictions: Cannot fly, has no ranged attack, and does not use ice magic.
- Map description: An abandoned outdoor arena surrounded by mountains.
- Intended tone: Accessible open-air adventure fantasy with hopeful
  exploration, nature reclaiming ancient ruins, quiet mystery, gentle
  melancholy, clear language, and vivid natural imagery.

## Ownership boundary

### Unity controls

- The scenario type and completion condition.
- The real enemy prefab and internal enemy ID.
- The number of enemies.
- The map, difficulty, statistics, rewards, spawning, and combat.
- Progress tracking and the final success or failure state.

### The LLM may later generate

- Scenario title.
- Short introduction and motivation.
- Objective wording.
- Narrative display name for the enemy.
- Completion text.
- A short story summary for continuity with the next scenario.

### The LLM must not change

- `KillEnemies` into another scenario type.
- The target count of five.
- The enemy's actual abilities or visual identity.
- Difficulty, statistics, rewards, drops, or any other gameplay mechanics.

## First playable flow

1. The player starts `kill_torch_01`.
2. Unity displays its narrative wrapper.
3. Unity tracks kills whose internal target ID is `enemy_torch`.
4. Progress advances from `0 / 5` to `5 / 5`.
5. Unity completes the scenario and grants 15 EXP and 10 gold.
6. Unity displays the generated completion text.

## Acceptance criteria for Step 1

- The first scenario is unambiguous and mechanically fixed.
- It matches the five `Enemy_Torch` instances currently placed in `Arena`.
- LLM-owned narrative data is clearly separated from Unity-owned gameplay data.
- Additional scenario types, random selection, and runtime LLM integration remain
  outside the Step 1 scope.

# Step 13 — Narrative Continuity

## Goal

Let a newly generated scenario reference the player's completed narrative
history without allowing the LLM to change gameplay.

## Flow

1. Unity sends an empty `previousStorySummary` for the first scenario.
2. The LLM returns a narrative plus a compact `storySummary`.
3. Unity saves that summary only when the scenario is completed.
4. The next scenario request includes the saved summary.
5. The LLM uses one or two relevant details and returns a new rolling summary.

## Safety boundary

The history may influence titles, motivations, names, and completion prose. It
cannot change scenario type, target ID, target count, abilities, map facts,
difficulty, statistics, drops, or rewards.

## Acceptance criteria

- Starting but abandoning a scenario does not update history.
- Completing a scenario saves its `storySummary`.
- The saved summary survives a Unity Play Mode restart.
- The next request contains the saved summary.
- Request IDs, latency, token usage, and estimated cost remain traceable.
- The generated objective still preserves all Unity-owned gameplay facts.

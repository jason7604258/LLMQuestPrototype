# Step 17 — Experiment Lifecycle Records

## Goal

Join narrative generation evidence to what Unity actually displayed and what
the player did. These records support later dissertation analysis without
allowing the LLM to control gameplay.

## Output

The backend appends all records to:

```text
Backend/logs/narrative_runs.jsonl
```

New records use `schemaVersion: 2`. Every scenario run shares one `requestId`
across the following record types:

1. `generation`: fixed scenario facts, continuity input, prompt version, model,
   raw structured model output, validation status, returned narrative, latency,
   token counts, and estimated cost.
2. `gameplay_event` with `eventType: scenario_started`: confirms that Unity
   accepted a narrative and activated the fixed gameplay targets.
3. `gameplay_event` with `eventType: scenario_completed`: records final progress
   and the number of seconds from scenario activation to completion.

If a run contains `scenario_started` but no matching `scenario_completed`, it
can be treated as started but not completed. Old schema-version-1 generation
records remain valid historical data but do not contain lifecycle events.

## Validation and fallback evidence

Generation records distinguish the raw structured OpenAI output from the final
validated narrative. They record whether that output passed backend validation
and why OpenAI fell back when it did not.

Gameplay events additionally record whether Unity accepted the backend
narrative. If Unity uses its local fallback, the event includes the validation
error when applicable and the fallback reason.

## Cost

Lifecycle reporting is an ordinary local HTTP request. It does not call the
LLM, consume tokens, or add OpenAI API cost.

## Manual acceptance test

1. Restart the backend so it exposes `/record-run-event`.
2. Enter Play Mode, start one scenario, and complete it.
3. Run:

   ```bash
   tail -n 3 Backend/logs/narrative_runs.jsonl
   ```

4. Confirm the final three new lines share the same `requestId` and have this
   order:

   ```text
   generation
   scenario_started
   scenario_completed
   ```

5. Confirm the completion record has `completed: true`, matching
   `currentProgress` and `requiredAmount`, plus a positive `elapsedSeconds`.


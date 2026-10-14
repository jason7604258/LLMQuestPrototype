# Step 14 — LLM Experiment Logging

## Goal

Create reproducible evidence for evaluating narrative generation without
placing credentials or gameplay control in the dataset.

## Output

The backend writes one JSON object per line to
`Backend/logs/narrative_runs.jsonl`. JSONL allows results to be appended during
play and later loaded into Python, R, spreadsheets, or statistical tools.

## Recorded fields

- UTC timestamp and request ID
- generation source and selected model
- whether OpenAI was attempted and any fallback reason
- fixed Unity scenario facts
- previous story summary and tone
- all seven generated narrative fields
- OpenAI and total backend latency
- input, cached, cache-write, output, and total tokens
- estimated Standard short-context cost

## Privacy and reliability

- API keys and HTTP credentials are not recorded.
- Request IDs are tracing identifiers, not player identifiers.
- Records are written under a process lock to keep concurrent requests from
  mixing on the same line.
- Logging failure never blocks the gameplay response.

## Acceptance criteria

- Each valid request produces exactly one parseable JSONL line.
- OpenAI and fallback results are distinguished.
- Continuity input and generated output can be compared later.
- Token, latency, and cost fields support model evaluation.
- No API key appears in the record.

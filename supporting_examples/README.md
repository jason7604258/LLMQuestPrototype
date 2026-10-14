# Recorded narrative examples

Two consecutive Terra model records within the selected dataset, at lines 1 and 4 of Backend/logs/terra_gameplay_run01.jsonl. Their start/completion records are at lines 2/3 and 5/6. Exact fields, source hashes and identifiers are in input_output_examples.json. Both records have model, backend and Unity acceptance and recorded completion.

The second input summary equals the first output storySummary. Both use the same tone, printed once in the dissertation appendix. Both outputs use Torch Warden as the display name, but the second scenario is KillEnemies and targetId enemy_torch; the display name does not change gameplay type.

The system and user prompt text files are reconstructions from recorded inputs and the current Backend/app.py template labelled narrative-wrapper-v4. Logs do not retain complete historical API messages. requestId is omitted from user message data. The seven-field schema is supplied separately. Response JSON contains the recorded strings without rewriting. No model API was called for this extraction.

## Message roles

Each model request sends two messages together. system_prompt_reconstructed.txt supplies the system message. Each example_N_user_prompt_reconstructed.txt supplies the user message for that example, including its tone field. The tone is not a third message. The response schema is supplied separately through text_format. Appendix D labels the two message roles explicitly. These role labels are explanatory text and do not change the reconstructed message files.

# Narrative service and analysis

The submission instructions are in [the project README](../README.md).
Start `app.py` for the local HTTP service. Without an API credential it supplies
predefined fallback text; Unity retains control of quest mechanics.

`analyze_experiments.py` is the earlier operational/character-overlap analysis.
Its historical similarity bands are not validated narrative-quality thresholds.
The dissertation's later text comparison uses `analyze_lexical_similarity.py`
and `analyze_semantic_similarity.py`, with introductions and completion messages
analysed separately. Use `../Tools/reproduce_saved_comparison.py` from the project
root as documented in the README to check and recalculate the saved comparison.

Keep new runtime data and analysis outputs separate from the supplied study
logs and reports. The reports are evidence from recorded runs, not output from
the submission packaging process.

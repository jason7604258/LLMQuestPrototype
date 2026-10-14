# Historical analysis sources

These six files preserve the exact Python source bytes that existed before submission comments were added. The corresponding files one directory above have additional plain English comments only. Their abstract syntax trees are unchanged; original and documented hashes are recorded in `source_hashes.json`.

The original `run_model_analysis.py` and `analyze_model_comparison.py` hashes match the retained `comparison_metadata.json`. Keep these historical copies and all saved report metadata unchanged. Do not run these copies directly from this directory because their relative file locations assume the normal Backend directory.

The three byte-pinned metric modules remain unchanged in Backend: `analyze_experiments.py`, `analyze_lexical_similarity.py` and `analyze_semantic_similarity.py`. Their comments are explained in the project documentation rather than by rewriting these historical source files.

Use `python3 Tools/reproduce_saved_comparison.py` from the project root to verify the saved source/data hashes and recalculate the four-model tables in a new directory. This uses existing semantic scores and does not rerun the embedding model or contact a model API.

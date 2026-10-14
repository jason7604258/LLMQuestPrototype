# Saved comparison reproduction

From the extracted project root, using Python 3.10 or later:

```bash
python3 Tools/reproduce_saved_comparison.py
```

This standard-library helper verifies the historical algorithm sources, original log prefixes, selected record bytes, saved pair identities, lexical scores, semantic score files and report hashes. It then recalculates scenario means, macro and pooled means, correlations and diagnostic selections. All four resulting CSV files must match the retained tables exactly before results are published.

Results are written to the new directory `ReproducedReports/saved_comparison`. To run again, choose another new directory:

```bash
python3 Tools/reproduce_saved_comparison.py --output-dir ReproducedReports/another_check
```

Existing output directories and protected source/data directories are rejected. No original report, log or source file is rewritten. Historical absolute paths are not followed: required inputs are located within this extracted project. Where personal paths were removed from packaged metadata, `Docs/PACKAGING_CHANGES.json` links the original and packaged file hashes. Raw narrative and score files must still match their original hashes directly.

The helper uses the unchanged metric modules and the documented runner/comparator after verifying that their executable syntax matches the retained historical sources. It does not call their original command-line entry points, which require the original embedding environment. Their `verify_environment` function is not replaced or weakened.

This reproduces calculations **from saved semantic scores**. It does not load MPNet, regenerate embeddings, download files, call the narrative API, read `.env`, or demonstrate identical embedding results on a different machine. New metadata identify this as `relocated-saved-score-recomputation-v1` and record the Python version used for this run. Descriptions of model/runtime settings in the report refer to the retained historical records.

Run the six helper checks separately from the original backend test suite:

```bash
python3 -m unittest discover -s Tools -p 'test_reproduce_saved_comparison.py'
```

These checks use temporary relocated copies, verify unchanged input bytes and test rejection of changed scores, changed source behaviour, unrecorded metadata edits and unsuitable output paths. They do not add to or replace the historical 74-test result cited in the dissertation.

For new embedding calculations, the original semantic script and pinned requirements remain available. Use a fresh output directory and obtain the documented MPNet revision separately. The retained four-model runner additionally enforces Python 3.11.2, the recorded package versions and the historical model-cache location; it is retained as historical source, not presented as a portable one-command embedding rerun.

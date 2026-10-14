# Submission verification: 18 September 2026

These checks apply to the prepared source archive. They are separate from the
9 and 10 September verification records cited in the dissertation.

## Source changes

- All 39 project C# scripts were compared with the working-project copies.
  After removing full-line comments, their remaining lines were identical.
- All 14 existing Python source/test files were compared using Python abstract
  syntax trees. The trees were identical, excluding source line positions.
- Three analysis modules checked by historical hashes were kept byte for byte:
  `analyze_experiments.py`, `analyze_lexical_similarity.py` and
  `analyze_semantic_similarity.py`.
- Original versions of the six newly documented analysis/test files are retained
  under `Backend/historical_analysis_sources/`. No gameplay or existing analysis
  calculation was changed.

## Tests and saved results

The existing backend and analysis suite was run against this submission copy
using Python 3.11.2 and an empty API-key environment variable:

```bash
OPENAI_API_KEY='' python -m unittest discover -s Backend -p 'test_*.py' -v
```

**74 tests passed**. Provider calls were simulated. The first restricted run
could not bind the temporary loopback test server; the successful run allowed
that local socket. Neither run generated new narratives.

The separate portable-helper suite passed **6 tests**. It checks a relocated
project and rejection of changed scores, changed source behaviour, unrecorded
metadata edits, existing output and protected output locations.

The helper recalculated all four comparison CSV files from the supplied saved
scores. The scenario table, macro/pooled table, correlation table and diagnostic
cases matched the saved files byte for byte. These checks do not rerun MPNet or
verify a new model API response.

## Data and packaging

- The four source JSONL logs and numerical CSV evidence match the working-project
  originals. Luna's failed request remains in the preserved source log.
- Sixteen report/metadata copies replace local account paths with placeholders.
  `PACKAGING_CHANGES.json` records the original and packaged file hashes. This
  does not change narrative text, pair scores or historical checksums stored as
  evidence. Historical file hashes are not presented as hashes of the relocated
  metadata copies.
- External asset omissions are listed individually in `OMITTED_ASSETS.csv`.
  Their paired `.meta` files are preserved. The original working project and its
  external artwork were not changed.
- Environment files containing live credentials, virtual environments, caches,
  editor history and dissertation files are excluded. The included `.env.example`
  has an empty API-key field.
- `SUBMISSION_MANIFEST.json` at the project root identifies the packaged files
  and their SHA-256 hashes. It does not include its own hash.

A fresh Unity build or gameplay session was not run from this asset-reduced
archive. External assets must be restored before opening it in Unity. Software
tests and comment comparisons do not replace that integration check.

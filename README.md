# LLM Quest Prototype: source code and supporting records

This repository is a curated source snapshot prepared for GitHub from the
dissertation code submission on 14 October 2026. It contains the Unity project
source, the local Python narrative service, software tests, and the recorded data
used for the four-model comparison. The dissertation PDF is submitted separately.
The snapshot also includes the later backend health response update and its test.

## Start here

- **Read the implementation:** begin with `Assets/Scripts/Quests/QuestManager.cs`
  and `Backend/app.py`.
- **Run the Python service or tests:** follow the commands below. No game artwork
  or embedding model is needed for these steps.
- **Understand the Unity game limitation:** this is a source archive, not a
  playable game. A fresh clone cannot run the complete game because external
  artwork and other assets are omitted. Some artwork cannot be redistributed as
  raw assets under the recorded terms; other artwork has unresolved provenance.
  See `Docs/THIRD_PARTY_NOTICES.md` and `Docs/OMITTED_ASSETS.csv`. The original
  local development project is separate from this GitHub copy.
- **Inspect the saved results:** open
  `Backend/reports/model_comparison_v1/model_comparison.md`. Run
  `python3 Tools/reproduce_saved_comparison.py` to check calculations from the
  saved scores. This does not generate new model responses or embeddings.

## Contents

| Location | Contents |
| --- | --- |
| `Assets/Scripts/` | Player, combat, inventory, scene and quest code |
| `Assets/Scenes/`, `Assets/Prefabs/` | Scene and object configuration |
| `Packages/` | Unity package manifest and dependency lock |
| `ProjectSettings/` | Unity version, input, build and project settings |
| `Backend/app.py` | Local narrative service and deterministic fallback |
| `Backend/test_*.py` | Backend and analysis tests |
| `Backend/logs/` | Four preserved source logs used in the dissertation |
| `Backend/reports/` | Selected inputs, similarity scores and saved reports |
| `Backend/historical_analysis_sources/` | Original versions of analysis scripts that received comments for submission |
| `Tools/` | A portable check and recalculation of the saved comparison |
| `supporting_analysis/` | Dated test record, price basis and comparison tables referenced in the dissertation |
| `supporting_examples/` | Recorded input/output examples and explicitly reconstructed prompts |
| `Docs/` | Development notes, attribution and packaging information |

The development notes describe different stages of the project. They are not a
claim that every earlier setting or planned feature is present in the final game.

## Python setup

Python 3.11 is recommended. The recorded semantic analysis used Python 3.11.2;
its exact package versions are listed in `Backend/requirements-semantic.txt`.
The backend requirements are separate from these larger analysis dependencies.

From the extracted project directory, on macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r Backend/requirements.txt
```

On Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r Backend/requirements.txt
```

## Run the narrative service

For a first check, use fallback mode. On macOS or Linux:

```bash
OPENAI_API_KEY='' python Backend/app.py
```

On PowerShell, run `$env:OPENAI_API_KEY = ''` and then
`python Backend/app.py`. Do not create a `.env` file containing a key for this
fallback check. With no credential, the service returns predefined narrative
text. This checks the integration but does not generate new LLM text.

The default address is `http://127.0.0.1:8000`. A health check is available at
`http://127.0.0.1:8000/health`. Stop the service with Ctrl+C. If port 8000 is
occupied, stop the other service or use `--port` and update both endpoint fields
on Unity's `NarrativeApiClient` to the same port.

To request new model text, copy `Backend/.env.example` to `Backend/.env`, enter
your own `OPENAI_API_KEY`, and set `OPENAI_MODEL` to a model available to your
account. The implemented default is `gpt-5.6-sol`. Remove an empty API-key
override from the shell before starting this mode. The backend loads `.env`
without overriding an existing environment variable. New requests use the
external service and may incur charges. No live credential is included here.

New runtime records go to `Backend/logs/narrative_runs.jsonl`. This file is
separate from the four saved study logs. `NARRATIVE_LOG_ENABLED=0` disables new
logging; `NARRATIVE_LOG_PATH` selects another file.

## Unity project status

This GitHub repository does not include a playable build, and its stripped Unity
project cannot run the complete game as downloaded. The missing assets are not
supplied here. A clean-clone build has not been validated. The original local
development project, which retains its assets, was not changed by this export.
The restoration notes in `Docs/THIRD_PARTY_NOTICES.md` are for people who
already have appropriate access to matching files; they are not a way to obtain
the omitted assets from this repository.

For reference, the original project uses **Unity 6000.5.0f1**, as recorded in
`ProjectSettings/ProjectVersion.txt`, and its main scene is
`Assets/Scenes/Arena.unity`. The saved configuration includes the shared player
and quest systems. Input handling is set to **Both**. Movement, combat and
several panels use `ProjectSettings/InputManager.asset`; shop interaction uses
`Assets/InputSystem_Actions.inputactions`. With the original dependencies and
Python service available, the automatic quest loop requests a narrative, checks
it and activates a predefined scenario. A Forest objective can appear while the
player is still in Arena; its targets are prepared on arrival in Forest. Matching
gameplay events advance progress, and completion saves the story summary for the
next request.

| Control | Action |
| --- | --- |
| WASD or arrow keys | Move and set the facing/aim direction |
| J | Sword attack when equipped |
| Q | Switch equipment |
| L or right mouse button | Bow attack when equipped |
| Escape | Toggle the stats panel |
| K | Toggle the skill tree |
| E near a shopkeeper | Interact with the shop |
| Left click an inventory slot | Use an item, or sell it in the relevant shop state |
| Right click an inventory slot | Drop an item |

The current prototype grants the configured quest experience reward when the
experience manager is available. Quest gold values are configured but are not
connected to quest completion. This is distinct from inventory/shop currency.

The latest completed story summary can persist between Play sessions. To clear
it, use **Clear Narrative History** in the `QuestManager` Inspector component
menu. This does not delete the saved JSONL study logs. If the backend is absent
or its response is unusable, Unity can use `NarrativeTestProvider` locally.

## Run the tests

After installing `Backend/requirements.txt`, run from the project root:

```bash
OPENAI_API_KEY='' python -m unittest discover -s Backend -p 'test_*.py' -v
```

On PowerShell, set an empty `OPENAI_API_KEY` first and run the same command
without the leading assignment. The tests replace model calls with simulated
responses. HTTP tests open a temporary loopback port; a sandbox that blocks
local sockets will prevent those tests from running. These tests do not launch
Unity or check live model behaviour. They do not need the MPNet download.

## Check the saved comparison without a model download

```bash
python Tools/reproduce_saved_comparison.py
```

This uses the saved scores and original comparison calculations. It checks the
selected logs, source hashes, field pairs and recorded analysis settings, then
recalculates the scenario means, overall means, correlations and diagnostic
cases in a new output directory. It does not encode the texts again or call a
model API. See the helper's `--help` for its output option.

The four source logs preserve the original chronological records, including
Luna's failed request. The selected comparison contains 72 generated narratives
per model. The first Luna fallback is excluded from text comparison, but remains
in its source log. The three files `analysis_manifest.json`,
`comparison_metadata.json` and `metric_disagreement_cases.csv` are included in
`Backend/reports/model_comparison_v1/`.

## Recalculate lexical and semantic scores

The original analysis programs are also included. Use fresh output directories
to avoid overwriting the submitted evidence. For the original Sol selection:

```bash
python Backend/analyze_lexical_similarity.py --output-dir Reanalysis/sol/lexical
python -m pip install -r Backend/requirements-semantic.txt
python Backend/analyze_semantic_similarity.py \
  --output-dir Reanalysis/sol/semantic \
  --lexical-pairs Reanalysis/sol/lexical/within_scenario_lexical_pairs.csv \
  --lexical-audit Reanalysis/sol/lexical/hash_ranked_audit_sample_40.csv \
  --allow-download
```

`--allow-download` is needed only when the exact MPNet revision is not already
cached. Omit it for subsequent offline runs. This downloads an embedding model;
it does not generate new quest narratives. The pinned model files and Python
environment are not bundled in this archive. Hardware and package differences
can affect numerical reproduction, so record the environment used for a new run.

The original `run_model_analysis.py` and `analyze_model_comparison.py` retain
their strict historical environment checks. They are not portable launchers:
their recorded paths refer to the original analysis location, now represented
by placeholders in the archive. Use the portable helper for the saved-score
comparison. A complete new embedding run requires setting up and checking the
recorded environment; it is separate from the saved-score check.

`Docs/ANALYSIS_GUIDE.md` explains the preserved analysis code and gives the
input paths and hashes for recalculating the other three datasets.

## What changed for submission

Existing comment style is preserved: short English comments describing purpose,
conditions and boundaries. Comments were added to analysis/test code and a few
misleading Unity comments were corrected. Original analysis sources whose
hashes are recorded were either kept unchanged or retained separately. The
original gameplay and analysis calculations were not changed.

The four raw logs and numerical CSV evidence are unchanged. Some report paths
contained a local computer account name. In the submitted copies only, these
paths use `<PROJECT_ROOT>` or `<MODEL_CACHE>`. `Docs/PACKAGING_CHANGES.json`
records both the historical and packaged hashes of each affected file; old
hashes inside historical reports still refer to their original files.

`SUBMISSION_MANIFEST.json` lists the files and hashes in this archive. Local
credentials, virtual environments, Unity caches, editor history, third-party
asset source packs and dissertation editing files are excluded. See
`Docs/THIRD_PARTY_NOTICES.md` for external software and assets, and
`Docs/SUBMISSION_VERIFICATION.md` for checks performed on this submission copy.

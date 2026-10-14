# Code Safety and Branch Audit

## Audit scope

- 41 project-owned Unity C# scripts under `Assets/Scripts`.
- 4 project-owned Python files in `Backend` (application, analyser, and tests).
- Unity/TextMesh Pro package examples were excluded because they are third-party code.
- Review method: branch inventory, call-path tracing, scene/prefab reference checks, Unity component guarantees, and automated build/tests.

The purpose of this audit was not to minimise the raw number of `if` statements. It was to remove only logic that cannot affect a valid execution, while retaining checks for failures that can realistically occur.

## Result

Two provably redundant branches were removed:

1. `Player_bow.ReleaseArrow()` checked whether the result of `Instantiate(arrowPrefab, ...)` was null. The prefab is checked before the call, and a successful generic Unity `Instantiate<T>` returns the created component. The second null test could not provide a recovery path.
2. `Inventory_Manager.DropItem()` performed the same post-`Instantiate` null check for `lootPrefab`. The prefab and drop origin are already validated before creation.

No functional behaviour was changed. Both methods still validate their configuration before spawning and still initialise the generated object in the same way.

## Branches that must remain

| Boundary | Representative scripts | Why the checks are necessary |
| --- | --- | --- |
| LLM and JSON | `NarrativeApiClient`, `NarrativeValidator`, `QuestManager`, `Backend/app.py` | Model output and HTTP responses are external inputs. They may be missing, malformed, contradictory, late, or unavailable. Validation and fallback are core experimental controls. |
| Scene lifecycle | `GameManager`, `SceneChanger`, `ConfinerFinder`, `ExpManager`, `StatsUI`, `PlayerHealth` | Objects and UI references are destroyed/recreated when scenes change. Singleton, duplicate, rebinding, and missing-scene checks cover real transitions. |
| Gameplay state | Player, enemy, arrow, and quest scripts | Cooldowns, death, ownership, collision, pending animation events, active scenario type, and progress limits prevent duplicate or invalid actions. |
| Transactions | Inventory, shop, and skill-tree scripts | Capacity, quantity, price, currency, level cap, and null-item checks prevent lost items or invalid purchases/upgrades. |
| Inspector/runtime setup | UI, prefabs, animation, and target reset scripts | References may be intentionally optional, created at runtime, or absent in an incomplete test scene. These checks turn setup mistakes into clear warnings or fallbacks. |
| Experiment logging | `QuestManager`, `NarrativeApiClient`, `Backend/app.py`, analyser | Request IDs, source/fallback state, completion events, and schema checks are required to interpret dissertation experiment data correctly. |

## Important retained safety nets

### LLM narrative pipeline

The following are intentional, not over-defensive:

- HTTP failure and timeout fallback to a local narrative.
- Required-field and maximum-length validation.
- Objective amount validation against Unity's fixed scenario data.
- Rejection of narrative data that changes gameplay facts.
- Request IDs to associate generation, scenario-started, and scenario-completed records.
- Empty-history handling for the first scenario.

These branches enforce the project boundary: Unity controls mechanics and balance; the LLM controls only the narrative wrapper.

### Cross-scene persistence

Duplicate singleton cleanup and null/rebind checks remain because persistent objects survive while scene-owned objects do not. Removing these branches can produce duplicate managers, stale UI references, an unbound camera confiner, or missing player data after a transition.

### Animation and dynamically generated UI

Animation Event fallbacks and optional UI-reference checks remain. Animation events may be emitted more than once by a Blend Tree or may be absent from an incorrectly configured clip. Runtime UI objects may also be recreated after a scene change.

## Checks deliberately not removed

Some scripts use `[RequireComponent]` and then still check the component reference. These checks look redundant in a fully configured prefab, but they provide safe behaviour in editor-time migration, incomplete test objects, and legacy scene data. Removing them would save very few lines while making setup failures harder to diagnose.

Public compatibility methods were also retained even when no current scene or prefab invokes them. Removing a public method based only on serialized-reference search could break an Animation Event, UnityEvent, or future Inspector connection without a meaningful presentation benefit.

## Presentation summary

### Chinese

我審查了 41 支 Unity C# 程式與 4 支 Python backend 程式。我沒有單純追求減少 `if` 的數量，而是依照實際失敗邊界分類。最後只移除了兩個可以由 Unity `Instantiate` 行為證明永遠不會觸發的重複判斷。LLM、網路、跨場景生命週期、遊戲狀態與交易資料的驗證都保留，因為這些錯誤在實際執行中可能發生，也直接影響遊戲正確性與實驗資料可信度。

### English

I audited 41 Unity C# scripts and four Python backend files. Rather than reducing the number of `if` statements indiscriminately, I classified them by real failure boundary. I removed only two branches that were provably unreachable under Unity's instantiation guarantees. Validation at the LLM, network, scene-lifecycle, gameplay-state, and transaction boundaries was retained because those failures are realistic and directly affect correctness and experimental reliability.

## Verification

The final audit was verified with:

```text
dotnet build --no-restore Assembly-CSharp.csproj
dotnet build --no-restore Assembly-CSharp-Editor.csproj
cd Backend
.venv/bin/python -m unittest test_app.py test_analyze_experiments.py
```

Results:

- Unity runtime scripts: build succeeded with 0 errors.
- Unity editor scripts: build succeeded with 0 errors.
- Backend and experiment analyser: 19 tests passed.
- The standalone .NET build reports Roslyn analyser-version warnings because its compiler is older than Unity's bundled analyser. These are tool-version warnings, not project-code errors.

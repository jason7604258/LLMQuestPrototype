#!/usr/bin/env python3
"""recalculate saved comparison tables without loading a model or calling an api"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile


PROJECT = Path(__file__).resolve().parents[1]
BACKEND = PROJECT / "Backend"
REPORTS = BACKEND / "reports"
REFERENCE = REPORTS / "model_comparison_v1"
HISTORICAL = BACKEND / "historical_analysis_sources"
REFERENCE_METADATA_SHA256 = "33beb47efe7bad1f33ad0828e76586ffad9044dcc2a9f88420343c2d9ab5169d"
TABLE_NAMES = (
    "scenario_comparison.csv", "model_macro_summary.csv",
    "pair_correlations.csv", "metric_disagreement_cases.csv",
)


# hash files as bytes so text encoding and newline changes cannot pass unnoticed
def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# retain clear errors instead of silently omitting a failed provenance check
def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


# read only explicitly named package files, never the old absolute metadata paths
def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected a JSON object: {path.name}")
    return value


# personal path redactions have separate original and packaged byte hashes
def packaging_changes() -> dict[str, dict]:
    path = PROJECT / "Docs" / "PACKAGING_CHANGES.json"
    if not path.is_file():
        return {}
    entries = read_json(path).get("files", [])
    require(isinstance(entries, list), "Packaging changes must contain a files list")
    result = {}
    for entry in entries:
        require(isinstance(entry, dict) and isinstance(entry.get("path"), str),
                "Invalid packaging change entry")
        name = entry["path"]
        require(name not in result, f"Duplicate packaging entry: {name}")
        result[name] = entry
    return result


# only metadata may use a documented path-redaction mapping; data remain exact
def verify_file(path: Path, expected: str, changes: dict, redactions: list,
                allow_redaction: bool = False) -> None:
    require(path.is_file(), f"Required file is missing: {path.relative_to(PROJECT)}")
    actual = digest(path)
    if actual == expected:
        return
    relative = path.relative_to(PROJECT).as_posix()
    change = changes.get(relative, {}) if allow_redaction else {}
    require(change.get("originalSha256") == expected
            and change.get("packagedSha256") == actual
            and bool(change.get("reason")),
            f"Hash mismatch: {relative}")
    if relative not in redactions:
        redactions.append(relative)


# inserted comments must not alter the executable structure of a historical script
def verify_documented_source(name: str, expected: str) -> dict:
    historical = HISTORICAL / name
    active = BACKEND / name
    require(historical.is_file() and digest(historical) == expected,
            f"Historical source hash differs: {name}")
    original_tree = ast.dump(ast.parse(historical.read_text(encoding="utf-8")),
                             include_attributes=False)
    active_tree = ast.dump(ast.parse(active.read_text(encoding="utf-8")),
                           include_attributes=False)
    require(active_tree == original_tree, f"Documented source changed behaviour: {name}")
    return {"historicalSha256": expected, "packagedSha256": digest(active),
            "abstractSyntaxTreeMatches": True}


# check algorithm identity before importing any project analysis module
def verify_sources(comparison: dict, baseline: dict, lexical: dict) -> dict:
    expected = {
        "analyze_experiments.py": lexical["normalizationDependencySha256"],
        "analyze_lexical_similarity.py": baseline["lexicalAnalyzerSha256"],
        "analyze_semantic_similarity.py": baseline["analyzerSha256"],
    }
    result = {}
    for name, value in expected.items():
        path = BACKEND / name
        require(path.is_file() and digest(path) == value,
                f"Pinned algorithm source hash differs: {name}")
        result[name] = {"historicalSha256": value, "packagedSha256": value,
                        "exactBytesMatch": True}
    for name, key in (("run_model_analysis.py", "runnerSha256"),
                      ("analyze_model_comparison.py", "analyzerSha256")):
        result[name] = verify_documented_source(name, comparison[key])
    return result


# permit new reports only outside source, data, documentation and tooling folders
def output_destination(value: Path) -> Path:
    candidate = value.expanduser().absolute()
    require(not any(p.is_symlink() for p in (candidate, *candidate.parents)),
            "Output location must not use a symbolic link")
    destination = candidate.resolve()
    for name in ("Backend", "Assets", "Packages", "ProjectSettings", "Tools", "Docs"):
        protected = (PROJECT / name).resolve()
        require(destination != protected and protected not in destination.parents,
                f"Output must be outside {name}")
    require(not destination.exists(),
            "Output directory already exists; choose a new directory")
    return destination


# replace only known location fields in memory; saved metadata are never rewritten
def relocated_cohort(original: dict, specification: tuple) -> dict:
    label, _, filename, _, _, _ = specification
    require(original["label"] == label, "Cohort labels or order differ")
    item = copy.deepcopy(original)
    item["sourcePath"] = str(BACKEND / "logs" / filename)
    if label == "Sol":
        item["inputPath"] = item["sourcePath"]
        item["lexicalDirectory"] = str(REPORTS / "lexical_frozen72_v3")
        item["semanticDirectory"] = str(REPORTS / "semantic_frozen72_v1")
    else:
        directory = REFERENCE / label.lower()
        item["inputPath"] = str(directory / "input_frozen72.jsonl")
        item["lexicalDirectory"] = str(directory / "lexical")
        item["semanticDirectory"] = str(directory / "semantic")
    return item


# identify all checked input tables using package locations instead of saved paths
def cohort_source_paths(cohort: dict) -> dict[str, Path]:
    lexical = Path(cohort["lexicalDirectory"])
    semantic = Path(cohort["semanticDirectory"])
    return {
        "lexicalMetadata": lexical / "analysis_metadata.json",
        "semanticMetadata": semantic / "analysis_metadata.json",
        "lexicalPairs": lexical / "within_scenario_lexical_pairs.csv",
        "semanticPairs": semantic / "within_scenario_semantic_pairs.csv",
        "lexicalAudit": lexical / "hash_ranked_audit_sample_40.csv",
        "semanticAudit": semantic / "hash_ranked_audit_sample_40_with_semantic.csv",
        "embeddingManifest": semantic / "embedded_text_manifest.csv",
    }


# generated metadata use relative paths so the new result can move with its package
def relative_paths(value, destination: Path):
    if isinstance(value, dict):
        return {k: relative_paths(v, destination) for k, v in value.items()}
    if isinstance(value, list):
        return [relative_paths(v, destination) for v in value]
    if isinstance(value, str) and value.startswith(str(PROJECT) + os.sep):
        return Path(os.path.relpath(value, destination)).as_posix()
    return value


# reuse the original validation and calculation functions on authenticated saved rows
def reproduce(destination: Path) -> dict:
    changes, redactions = packaging_changes(), []
    comparison_path = REFERENCE / "comparison_metadata.json"
    verify_file(comparison_path, REFERENCE_METADATA_SHA256, changes, redactions, True)
    comparison = read_json(comparison_path)
    manifest_path = REFERENCE / "analysis_manifest.json"
    verify_file(manifest_path, comparison["manifestSha256"], changes, redactions, True)
    manifest = read_json(manifest_path)
    sol_sources = next(c["sources"] for c in comparison["cohortChecks"] if c["label"] == "Sol")
    baseline_path = REPORTS / "semantic_frozen72_v1" / "analysis_metadata.json"
    lexical_path = REPORTS / "lexical_frozen72_v3" / "analysis_metadata.json"
    verify_file(baseline_path, sol_sources["semanticMetadata"]["sha256"], changes, redactions, True)
    verify_file(lexical_path, sol_sources["lexicalMetadata"]["sha256"], changes, redactions, True)
    baseline = read_json(baseline_path)
    lexical = read_json(lexical_path)
    source_checks = verify_sources(comparison, baseline, lexical)

    # these modules use standard-library imports; their model-loading main functions are not run
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(BACKEND))
    runner = importlib.import_module("run_model_analysis")
    analyzer = importlib.import_module("analyze_model_comparison")
    require(len(manifest["cohorts"]) == len(runner.COHORTS) == 4,
            "Expected four selected cohorts")
    require(len(comparison["cohortChecks"]) == 4, "Expected four historical cohort checks")
    historical_checks = {c["label"]: c for c in comparison["cohortChecks"]}
    require(len(historical_checks) == 4, "Duplicate historical cohort labels")
    relocated = copy.deepcopy(manifest)
    relocated["cohorts"] = [relocated_cohort(c, spec)
                            for c, spec in zip(manifest["cohorts"], runner.COHORTS)]
    scenarios, macros, correlations, gaps, checks = [], [], [], [], []
    for cohort, specification in zip(relocated["cohorts"], runner.COHORTS):
        sources = historical_checks[cohort["label"]]["sources"]
        for name, path in cohort_source_paths(cohort).items():
            verify_file(path, sources[name]["sha256"], changes, redactions,
                        name in {"lexicalMetadata", "semanticMetadata"})
        # load_cohort rebuilds lexical scores and verifies source-prefix bytes, pair identity and shared settings
        rows, check = analyzer.load_cohort(cohort, specification, baseline)
        scenario_rows, macro_rows = analyzer.summarize(
            cohort["label"], rows, cohort["scenarioGenerationCounts"])
        correlation_rows, gap_rows = analyzer.correlations_and_gaps(
            cohort["label"], rows, scenario_rows)
        scenarios.extend(scenario_rows)
        macros.extend(macro_rows)
        correlations.extend(correlation_rows)
        gaps.extend(gap_rows)
        checks.append(check)

    tables = dict(zip(TABLE_NAMES, (scenarios, macros, correlations, gaps)))
    # authenticate the saved expected tables before comparing newly calculated bytes
    for name in TABLE_NAMES:
        verify_file(REFERENCE / name, comparison["outputs"][name]["sha256"], {}, [])
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".saved-comparison-", dir=destination.parent) as temporary:
        temporary_path = Path(temporary)
        results = {}
        for name, rows in tables.items():
            path = temporary_path / name
            analyzer.write_csv(path, rows)
            require(path.read_bytes() == (REFERENCE / name).read_bytes(),
                    f"Recalculated values differ from the saved table: {name}")
            results[name] = {"rows": len(rows), "sha256": digest(path),
                             "exactSavedTableMatch": True}

        # describe this run separately from historical model generation and embedding execution
        relocated["reproductionKind"] = "relocated-saved-score-recomputation-v1"
        relocated["historicalManifestSha256"] = comparison["manifestSha256"]
        relocated["packagedManifestSha256"] = digest(manifest_path)
        portable_manifest = relative_paths(relocated, destination)
        (temporary_path / "analysis_manifest.json").write_bytes(runner.json_bytes(portable_manifest))
        metadata = {
            "version": "relocated-saved-score-recomputation-v1",
            "scope": "Recalculation from saved pair scores; no new embeddings or model API requests.",
            "pythonVersionForThisRun": platform.python_version(),
            "helperSha256": digest(Path(__file__).resolve()),
            "packagedReferenceMetadataSha256": digest(REFERENCE / "comparison_metadata.json"),
            "sourceChecks": source_checks,
            "documentedMetadataRedactionsUsed": redactions,
            "sharedSemanticSettingsFromHistoricalRecords": comparison["sharedSemanticSettings"],
            "currentEmbeddingRuntimeChecked": False,
            "embeddingModelLoaded": False,
            "modelApiCalled": False,
            "cohortChecks": relative_paths(checks, destination),
            "outputs": results,
        }
        (temporary_path / "comparison_metadata.json").write_bytes(runner.json_bytes(metadata))
        note = (
            "> Relocated saved-score recomputation. The tables below were recalculated from "
            "verified saved pair scores and match the retained tables exactly. "
            "No embedding model was loaded and no narrative was generated. Runtime and "
            "model settings quoted below describe the historical records, not a new "
            "verification of the embedding environment.\n\n"
        )
        report = analyzer.render_report(portable_manifest, scenarios, macros, correlations, checks)
        (temporary_path / "model_comparison.md").write_text(note + report, encoding="utf-8")
        # publish only after every source and numerical equality check has succeeded
        destination.mkdir()
        for path in temporary_path.iterdir():
            shutil.move(str(path), destination / path.name)
    return metadata


# no credentials, cache downloads or historical-output overwrite options are needed
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=PROJECT / "ReproducedReports" / "saved_comparison")
    arguments = parser.parse_args()
    try:
        destination = output_destination(arguments.output_dir)
        result = reproduce(destination)
    except (OSError, ValueError, KeyError, TypeError, ImportError, StopIteration) as error:
        print(f"Saved-score reproduction stopped: {error}", file=sys.stderr)
        return 1
    print(f"Recalculated {len(result['outputs'])} tables; all match the saved bytes.\n{destination}")
    print("No model was loaded, no API request was made, and historical records were unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

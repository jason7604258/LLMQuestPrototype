#!/usr/bin/env python3
"""Freeze the planned gameplay cohorts and reuse the original offline analyzers.

Never generate narratives or download models. Raw logs and Sol reports are inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path

import analyze_lexical_similarity as lexical
import analyze_semantic_similarity as semantic
from analyze_experiments import get_record_type

BACKEND = Path(__file__).resolve().parent
DEFAULT_OUTPUT = BACKEND / "reports/model_comparison_v1"
SCENARIOS = lexical.FROZEN_SCENARIO_GENERATION_COUNTS
COHORTS = (
    ("Sol", "gpt-5.6-sol", "demo_narrative_runs_2026-08-20_take01.jsonl", 206,
     lexical.FROZEN_PREFIX_SHA256, ()),
    ("Terra", "gpt-5.6-terra", "terra_gameplay_run01.jsonl", 216,
     "2db1a0430dc58316d6419db420980d4c48468fad8b003b799ae36b30f1c13b1b", ()),
    ("Luna", "gpt-5.6-luna", "luna_gameplay_run01.jsonl", 217,
     "8bc6a5e357e89285df6a26a2c53d44bc80aed374219391c688fbf4cc2ca1592c", (1,)),
    ("Astra", "gpt-6-astra", "astra_gameplay_run01.jsonl", 216,
     "0c8529814f8adfae0100bc769964939be1cb8882f5376ce9ae05edae78f6a440", ()),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def save_frozen(path: Path, data: bytes) -> None:
    """An identical rerun is safe; a different existing artifact is not replaced."""
    if path.exists():
        require(path.read_bytes() == data, f"Existing frozen artifact differs: {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def check_output_directory(output: Path) -> None:
    """Never redirect derived artifacts into input logs or the original reports."""
    for parent in (output, *output.parents):
        require(not parent.is_symlink(), f"Symlinked output directory: {parent}")
    protected = [BACKEND / "logs", *(BACKEND / "reports" / name for name in
                 ("lexical_frozen72_v3", "semantic_frozen72_v1", "combined_frozen72_v1"))]
    resolved = output.resolve()
    for path in protected:
        require(resolved != path.resolve() and path.resolve() not in resolved.parents,
                f"Output overlaps protected source: {path}")
    if output.exists():
        require(not any(p.is_symlink() for p in output.rglob("*")),
                "Managed output contains a symlink; refusing to overwrite through it")


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def validate_generations(records: list[dict], model: str, counts: dict,
                         complete_run: bool) -> list[dict]:
    generations = [r for r in records if get_record_type(r) == "generation"]
    require(len(generations) == 72, f"{model}: expected 72 generations")
    by_id = {r["requestId"]: r for r in generations}
    require(len(by_id) == 72, f"{model}: duplicate request IDs")
    require(Counter(r["scenario"]["scenarioId"] for r in generations) == counts,
            f"{model}: unexpected scenario counts")
    for r in generations:
        require(r.get("model") == model and r.get("source") == "openai"
                and r.get("openaiAttempted") is True
                and r.get("modelOutput", {}).get("accepted") is True
                and r.get("validation", {}).get("returnedNarrativeAccepted") is True
                and not r.get("fallbackReason"),
                f"{model}: unexpected model, fallback or rejected output: {r['requestId']}")
        require(all(isinstance(r["narrative"].get(f), str)
                    and r["narrative"][f].strip() for f in lexical.LEXICAL_FIELDS),
                f"{model}: missing analyzed text")
    started, completed, seen = set(), set(), set()
    last_summary = ""
    for r in records:
        request = r["requestId"]
        if get_record_type(r) == "generation":
            continuity = r.get("continuity", {})
            # Sol has incomplete event logging; it remains the original frozen
            # cohort, not a retrospectively filtered "complete gameplay" run.
            if complete_run:
                require(continuity.get("previousStorySummary", "") == last_summary,
                        f"{model}: continuity mismatch: {request}")
            require(continuity.get("wasProvided") == bool(continuity.get("previousStorySummary", "")),
                    f"{model}: continuity flag mismatch: {request}")
            seen.add(request)
            # Event POSTs can arrive after the next generation response (Luna).
            # Compare the generation chain, then require every predecessor's
            # completion event to exist, rather than relying on log write order.
            last_summary = r["narrative"]["storySummary"].strip()
        else:
            require(get_record_type(r) == "gameplay_event" and request in seen,
                    f"{model}: unknown or orphan event")
            require(r.get("scenarioId") == by_id[request]["scenario"]["scenarioId"],
                    f"{model}: event scenario mismatch")
            require(r.get("narrativeSource") == "backend"
                    and r.get("unityValidation", {}).get("backendNarrativeAccepted") is True,
                    f"{model}: Unity rejected a narrative")
            event = r.get("eventType")
            require(event in ("scenario_started", "scenario_completed"),
                    f"{model}: unexpected event: {event}")
            target = started if event == "scenario_started" else completed
            require(request not in target, f"{model}: duplicate {event}")
            target.add(request)
            if event == "scenario_completed":
                require(request in started and r.get("completed") is True,
                        f"{model}: invalid completion")
    require(started == set(by_id), f"{model}: missing starts")
    require(len(completed) == (72 if complete_run else 62),
            f"{model}: unexpected completion count")
    return generations


def prepare(output: Path) -> dict:
    check_output_directory(output)
    entries, reference_facts = [], {}
    for label, model, filename, limit, expected, exclusions in COHORTS:
        source = BACKEND / "logs" / filename
        lines = source.read_bytes().splitlines(keepends=True)
        prefix = lines[:limit]
        require(len(prefix) == limit, f"{label}: source prefix is incomplete")
        lexical.verify_prefix_hash(sha256(b"".join(prefix)), expected)
        if exclusions:
            fallback = json.loads(prefix[0])
            require(fallback.get("requestId") == "760f00acb39244a2a577485a15356efa"
                    and fallback.get("source") == "fallback"
                    and fallback.get("fallbackReason") == "APIConnectionError: Connection error.",
                    "Unexpected Luna exclusion")
        selected = [(n, raw) for n, raw in enumerate(prefix, 1) if n not in exclusions]
        data = b"".join(raw for _, raw in selected)
        records = [json.loads(raw) for _, raw in selected]
        counts = dict(SCENARIOS) if label == "Sol" else {s: 9 for s in SCENARIOS}
        generations = validate_generations(records, model, counts, label != "Sol")
        for r in generations:
            sid = r["scenario"]["scenarioId"]
            facts = {k: r[k] for k in ("scenario", "tone", "promptVersion")}
            reference_facts.setdefault(sid, facts)
            require(reference_facts[sid] == facts, f"{label}: changed prompt/scenario facts")
        if label == "Sol":
            input_path = source
            lex_dir = BACKEND / "reports/lexical_frozen72_v3"
            sem_dir = BACKEND / "reports/semantic_frozen72_v1"
        else:
            input_path = output / label.lower() / "input_frozen72.jsonl"
            save_frozen(input_path, data)
            lex_dir = output / label.lower() / "lexical"
            sem_dir = output / label.lower() / "semantic"
        entries.append({
            "label": label, "requestedModel": model,
            "sourcePath": str(source), "sourcePrefixLines": limit,
            "sourcePrefixSha256": expected,
            "excludedPrefixLines": list(exclusions),
            "exclusionReason": "connection-error fallback; not model-generated text" if exclusions else None,
            "afterPrefixPolicy": "Exclude every subsequent record; retain unchanged in source log",
            "sourceFullSha256AtPreparation": sha256(b"".join(lines)),
            "sourcePhysicalLinesAtPreparation": len(lines),
            "sourceGenerationCountsByOriginAtPreparation": dict(Counter(
                r.get("source", "unknown") for raw in lines
                if get_record_type(r := json.loads(raw)) == "generation")),
            "excludedRecordsAtPreparation": [
                {"sourceLine": n, "requestId": r["requestId"],
                 "recordType": get_record_type(r), "eventType": r.get("eventType"),
                 "reason": "known connection-error fallback" if n in exclusions else "after fixed cohort boundary"}
                for n, raw in enumerate(lines, 1) if n in exclusions or n > limit
                for r in [json.loads(raw)]],
            "inputPath": str(input_path), "inputLines": len(selected),
            "inputSha256": sha256(data), "generationRecords": 72,
            "scenarioGenerationCounts": counts,
            "withinScenarioPairs": sum(n * (n - 1) // 2 for n in counts.values()),
            "completedEvents": 62 if label == "Sol" else 72,
            "continuityVerification": "empty initial context; every later generation matches preceding generation summary; all 72 completions present (event writes may arrive late)" if label != "Sol"
                else "not required: original frozen cohort has incomplete completion-event coverage",
            "sourceLineMapping": [{"inputLine": i, "sourceLine": n,
                                   "requestId": r["requestId"], "recordType": get_record_type(r)}
                                  for i, ((n, _), r) in enumerate(zip(selected, records), 1)],
            "lexicalDirectory": str(lex_dir), "semanticDirectory": str(sem_dir),
        })
    manifest = {
        "version": "gameplay-four-model-v1", "cohorts": entries,
        "selection": "Fixed chronological boundaries; no similarity-score selection",
        "fields": list(lexical.LEXICAL_FIELDS), "sampleSize": 40, "sampleSalt": "20260820",
        "primaryAggregation": "Equal arithmetic mean of eight scenario pair means",
    }
    save_frozen(output / "analysis_manifest.json", json_bytes(manifest))
    return manifest


def verify_environment() -> None:
    sol = json.loads((BACKEND / "reports/semantic_frozen72_v1/analysis_metadata.json").read_text())
    lex = json.loads((BACKEND / "reports/lexical_frozen72_v3/analysis_metadata.json").read_text())
    for filename, expected in (
        ("analyze_semantic_similarity.py", sol["analyzerSha256"]),
        ("analyze_lexical_similarity.py", sol["lexicalAnalyzerSha256"]),
        ("analyze_experiments.py", lex["normalizationDependencySha256"]),
    ):
        require(sha256((BACKEND / filename).read_bytes()) == expected,
                f"Analyzer changed since Sol: {filename}")
    require(platform.python_version() == sol["pythonVersion"], "Python version differs from Sol")
    for package, key in (
        ("sentence-transformers", "sentenceTransformersVersion"),
        ("transformers", "transformersVersion"), ("torch", "torchVersion"),
        ("numpy", "numpyVersion"), ("tokenizers", "tokenizersVersion"),
        ("huggingface-hub", "huggingfaceHubVersion"),
    ):
        require(importlib.metadata.version(package) == sol[key], f"Package differs from Sol: {package}")
    fingerprint, _ = semantic._snapshot_fingerprint(Path(sol["modelSnapshotPath"]))
    require(fingerprint == sol["modelSnapshotSha256"], "MPNet snapshot differs from Sol")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    try:
        check_output_directory(args.output_dir.absolute())
        verify_environment()
        manifest = prepare(args.output_dir.resolve())
        if not args.prepare_only:
            env = dict(os.environ, HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", OPENAI_API_KEY="")
            for cohort in manifest["cohorts"][1:]:
                for key in ("lexicalDirectory", "semanticDirectory"):
                    directory = Path(cohort[key])
                    check_output_directory(directory)
                    metadata = directory / "analysis_metadata.json"
                    if metadata.exists():
                        existing = json.loads(metadata.read_text())
                        require(existing.get("inputPrefixSha256") == cohort["inputSha256"],
                                f"Existing report belongs to a different input: {directory}")
                    else:
                        require(not directory.exists() or not any(directory.iterdir()),
                                f"Nonempty report directory lacks provenance: {directory}")
                common = ["--input", cohort["inputPath"], "--max-lines", str(cohort["inputLines"]),
                          "--expected-prefix-sha256", cohort["inputSha256"]]
                print(f"Analyzing {cohort['label']} offline", flush=True)
                subprocess.run([sys.executable, str(BACKEND / "analyze_lexical_similarity.py"),
                                *common, "--output-dir", cohort["lexicalDirectory"]], check=True, env=env)
                lex_dir = Path(cohort["lexicalDirectory"])
                subprocess.run([sys.executable, str(BACKEND / "analyze_semantic_similarity.py"),
                                *common, "--output-dir", cohort["semanticDirectory"],
                                "--lexical-pairs", str(lex_dir / "within_scenario_lexical_pairs.csv"),
                                "--lexical-audit", str(lex_dir / "hash_ranked_audit_sample_40.csv")],
                               check=True, env=env)
        print(args.output_dir.resolve() / "analysis_manifest.json")
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Analysis stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

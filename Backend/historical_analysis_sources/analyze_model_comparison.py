#!/usr/bin/env python3
"""Descriptive four-model comparison from verified, persisted offline pair CSVs."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

import analyze_lexical_similarity as lexical
import analyze_semantic_similarity as semantic
from run_model_analysis import (BACKEND, COHORTS, DEFAULT_OUTPUT, SCENARIOS,
                                json_bytes, require, sha256, validate_generations,
                                verify_environment, check_output_directory)

FIELDS = lexical.LEXICAL_FIELDS
METRICS = ("tokenLcsF1", "word3gramJaccard", "word1gramJaccard", "semanticCosine")
SHARED_SETTINGS = (
    "semanticMetricVersion", "analyzerSha256", "lexicalAnalyzerSha256",
    "fields", "modelId", "modelRevision", "modelSnapshotSha256", "embeddingDimension",
    "pooling", "modelMaxSequenceLength", "semanticPreprocessing", "normalizeEmbeddings",
    "cosineImplementation", "device", "dtype", "batchSize", "deterministicAlgorithms",
    "pythonVersion", "sentenceTransformersVersion", "transformersVersion", "torchVersion",
    "numpyVersion", "tokenizersVersion", "huggingfaceHubVersion", "offlineModelLoad",
)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def number(row: dict, key: str) -> float:
    try:
        result = float(row[key])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Missing or invalid number: {key}") from error
    require(math.isfinite(result), f"Non-finite number: {key}")
    return result


def validate_rows(rows: list[dict], counts: dict) -> None:
    seen, identities, pair_counts = set(), defaultdict(set), defaultdict(int)
    for row in rows:
        key = (*semantic.field_join_key(row)[:3], *sorted((row["requestIdA"], row["requestIdB"])))
        require(key not in seen, "Duplicate field pair")
        seen.add(key)
        require(row["comparisonScope"] == "within_scenario"
                and row["scenarioId"] in counts and row["field"] in FIELDS,
                "Unexpected scenario/field/scope")
        require(row["requestIdA"] != row["requestIdB"], "Self comparison")
        group = (row["scenarioId"], row["field"])
        identities[group].update((row["requestIdA"], row["requestIdB"]))
        pair_counts[group] += 1
        for metric in METRICS:
            score = number(row, metric)
            require((-1 if metric == "semanticCosine" else 0) <= score <= 1,
                    f"Out-of-range metric: {metric}")
    for scenario, n in counts.items():
        for field in FIELDS:
            require(len(identities[(scenario, field)]) == n
                    and pair_counts[(scenario, field)] == n * (n - 1) // 2,
                    "Incomplete scenario pair coverage")


def load_cohort(cohort: dict, specification: tuple, baseline: dict) -> tuple[list[dict], dict]:
    label, model, filename, limit, prefix_hash, exclusions = specification
    require(cohort["label"] == label and cohort["requestedModel"] == model,
            "Manifest model/order mismatch")
    source = BACKEND / "logs" / filename
    prefix = source.read_bytes().splitlines(keepends=True)[:limit]
    require(len(prefix) == limit and sha256(b"".join(prefix)) == prefix_hash,
            f"{label}: original prefix changed")
    data = b"".join(raw for i, raw in enumerate(prefix, 1) if i not in exclusions)
    input_path = Path(cohort["inputPath"])
    actual = b"".join(input_path.read_bytes().splitlines(keepends=True)[:cohort["inputLines"]])
    require(actual == data and sha256(data) == cohort["inputSha256"],
            f"{label}: derived input or input hash mismatch")
    counts = dict(SCENARIOS) if label == "Sol" else {s: 9 for s in SCENARIOS}
    require(cohort["scenarioGenerationCounts"] == counts, "Manifest scenario counts differ")
    generations = validate_generations([json.loads(raw) for raw in data.splitlines()],
                                      model, counts, label != "Sol")
    rebuilt = lexical.build_within_scenario_field_rows(generations)
    lex_dir, sem_dir = Path(cohort["lexicalDirectory"]), Path(cohort["semanticDirectory"])
    paths = {
        "lexicalMetadata": lex_dir / "analysis_metadata.json",
        "semanticMetadata": sem_dir / "analysis_metadata.json",
        "lexicalPairs": lex_dir / "within_scenario_lexical_pairs.csv",
        "semanticPairs": sem_dir / "within_scenario_semantic_pairs.csv",
        "lexicalAudit": lex_dir / "hash_ranked_audit_sample_40.csv",
        "semanticAudit": sem_dir / "hash_ranked_audit_sample_40_with_semantic.csv",
        "embeddingManifest": sem_dir / "embedded_text_manifest.csv",
    }
    lex_meta = json.loads(paths["lexicalMetadata"].read_text())
    meta = json.loads(paths["semanticMetadata"].read_text())
    for key in SHARED_SETTINGS:
        require(meta.get(key) == baseline[key], f"{label}: semantic setting mismatch: {key}")
    for info in (lex_meta, meta):
        require(info["inputPrefixSha256"] == cohort["inputSha256"]
                and info["inputPrefixHashVerified"] is True
                and info["generationRecords"] == 72
                and info["scenarioGenerationCounts"] == counts
                and info["malformedRecords"] == 0 and not info["loadErrors"],
                f"{label}: analysis metadata does not match input")
    require(lex_meta["analyzerSha256"] == meta["lexicalAnalyzerSha256"]
            and lex_meta["normalizationDependencySha256"] == sha256((BACKEND / "analyze_experiments.py").read_bytes()),
            f"{label}: lexical implementation changed")
    for name, meta_key in (("lexicalPairs", "lexicalPairsSha256"), ("lexicalAudit", "lexicalAuditSha256")):
        require(sha256(paths[name].read_bytes()) == meta[meta_key], f"{label}: {name} hash mismatch")
    lex_rows, rows = read_csv(paths["lexicalPairs"]), read_csv(paths["semanticPairs"])
    semantic.validate_lexical_manifest(rebuilt, lex_rows)
    semantic.validate_lexical_manifest(rebuilt, [{**r, "metricVersion": lexical.METRIC_VERSION} for r in rows])
    validate_rows(rows, counts)
    expected_pairs = sum(n * (n - 1) // 2 for n in counts.values())
    require(meta["withinScenarioPairs"] == expected_pairs and meta["fieldComparisons"] == 2 * expected_pairs,
            f"{label}: pair count mismatch")
    audit = read_csv(paths["lexicalAudit"])
    expected_audit, _ = lexical.build_audit_sample(rebuilt, 40, "20260820")
    require(len(audit) == 40 and len({semantic.pair_join_key(r) for r in audit}) == 40,
            f"{label}: audit size/duplicates")
    require([(semantic.pair_join_key(r), r["selectionHash"]) for r in audit] ==
            [(semantic.pair_join_key(r), r["selectionHash"]) for r in expected_audit],
            f"{label}: audit selection differs")
    enriched = semantic.enrich_audit_rows(audit, rows)
    persisted_audit = read_csv(paths["semanticAudit"])
    require(len(persisted_audit) == 40, f"{label}: semantic audit size")
    for expected, saved in zip(enriched, persisted_audit):
        for key, value in expected.items():
            require(abs(number(saved, key) - value) <= 5e-7 if isinstance(value, float)
                    else str(value) == saved.get(key), f"{label}: semantic audit changed: {key}")
    embedded = read_csv(paths["embeddingManifest"])
    identities = semantic.collect_text_identities(lex_rows)
    require(len(embedded) == len(identities) == meta["uniqueEmbeddedTexts"] == 144,
            f"{label}: embedding identity count")
    for expected, saved in zip(identities, embedded):
        for key in ("scenarioId", "field", "requestId", "text", "textSha256"):
            require(saved.get(key) == expected.get(key), f"{label}: embedded identity differs: {key}")
        require(saved["wouldTruncate"] == "False" and number(saved, "wordpieces") <= meta["modelMaxSequenceLength"],
                f"{label}: truncated text")
        require(abs(number(saved, "embeddingNorm") - 1) < 1e-5, f"{label}: non-unit embedding")
    require(meta["truncatedTextCount"] == 0
            and meta["maximumObservedWordpieces"] == max(int(r["wordpieces"]) for r in embedded),
            f"{label}: truncation metadata mismatch")
    embedded_by_key = {(r["scenarioId"], r["field"], r["requestId"]): r for r in embedded}
    for row in rows:
        for side in ("A", "B"):
            identity = embedded_by_key[(row["scenarioId"], row["field"], row["requestId" + side])]
            require(row["wordpieces" + side] == identity["wordpieces"]
                    and row["wouldTruncate" + side] == identity["wouldTruncate"],
                    f"{label}: pair embedding diagnostics mismatch")
    return rows, {"label": label, "generationRecords": 72, "withinScenarioPairs": expected_pairs,
                  "fieldComparisons": len(rows), "auditPairs": len(audit),
                  "maximumObservedWordpieces": meta["maximumObservedWordpieces"], "truncatedTextCount": 0,
                  "sources": {name: {"path": str(p), "sha256": sha256(p.read_bytes())} for name, p in paths.items()}}


def summarize(label: str, rows: list[dict], counts: dict) -> tuple[list[dict], list[dict]]:
    validate_rows(rows, counts)
    scenarios, macro = [], []
    for field in FIELDS:
        for scenario, count in counts.items():
            selected = [r for r in rows if r["scenarioId"] == scenario and r["field"] == field]
            scenarios.append({"model": label, "field": field, "scenarioId": scenario,
                              "generations": count, "pairs": len(selected),
                              **{m: statistics.mean(number(r, m) for r in selected) for m in METRICS}})
        selected = [r for r in rows if r["field"] == field]
        macro.append({"model": label, "field": field, "scenarios": len(counts), "pairs": len(selected),
                      **{m: statistics.mean(r[m] for r in scenarios if r["field"] == field) for m in METRICS},
                      **{"pooled_" + m: statistics.mean(number(r, m) for r in selected) for m in METRICS}})
    return scenarios, macro


def rank_percentiles(values: list[float]) -> list[float]:
    require(len(values) > 1, "Rank percentiles need at least two values")
    return [(rank - 1) / (len(values) - 1) for rank in semantic._average_ranks(values)]


def correlations_and_gaps(label: str, rows: list[dict], scenarios: list[dict]) -> tuple[list[dict], list[dict]]:
    correlations, gaps = [], []
    for field in FIELDS:
        selected = [r for r in rows if r["field"] == field]
        means = [r for r in scenarios if r["field"] == field]
        cosine = [number(r, "semanticCosine") for r in selected]
        for metric in METRICS[:-1]:
            lexical_values = [number(r, metric) for r in selected]
            correlations.append({"model": label, "field": field, "lexicalMetric": metric,
                                 "pairs": len(selected), "pairSpearman": semantic._spearman(cosine, lexical_values),
                                 "scenarioCount": len(means),
                                 "scenarioMeanSpearman": semantic._spearman(
                                     [r["semanticCosine"] for r in means], [r[metric] for r in means])})
        sem_pct = rank_percentiles(cosine)
        lcs_pct = rank_percentiles([number(r, "tokenLcsF1") for r in selected])
        ranked = sorted(range(len(selected)), key=lambda i: (-abs(sem_pct[i] - lcs_pct[i]), semantic.field_join_key(selected[i])))
        for index, i in enumerate(ranked[:5], 1):
            row = selected[i]
            gaps.append({"model": label, "field": field, "gapRank": index,
                         "absoluteRankPercentileGap": abs(sem_pct[i] - lcs_pct[i]),
                         "semanticRankPercentile": sem_pct[i], "lcsRankPercentile": lcs_pct[i],
                         "direction": "semantic_rank_higher" if sem_pct[i] > lcs_pct[i] else "lexical_rank_higher",
                         **{key: row[key] for key in ("scenarioId", "requestIdA", "requestIdB", "titleA", "titleB", "textA", "textB", *METRICS)}})
    return correlations, gaps


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: f"{v:.9f}" if isinstance(v, float) else v for k, v in row.items()})


def render_report(manifest: dict, scenarios: list[dict], macros: list[dict], correlations: list[dict], checks: list[dict]) -> str:
    lines = ["# Four-model lexical and semantic comparison", "",
             "Descriptive analysis of 72 generated narratives per model. Higher scores mean more similarity/overlap, not better or worse writing.", "",
             "## Main results: equal-scenario means", "",
             "Each scenario contributes 1/8. Introduction and completionText are separate; metrics are never averaged together.", "",
             "| Model | Field | Token LCS F1 | Word 3-gram Jaccard | Word 1-gram Jaccard | MPNet cosine |",
             "|---|---|---:|---:|---:|---:|"]
    for r in macros:
        lines.append(f"| {r['model']} | {r['field']} | " + " | ".join(f"{r[m]:.4f}" for m in METRICS) + " |")
    macro_lookup = {(r["model"], r["field"]): r for r in macros}
    completion_lcs = [r["tokenLcsF1"] for r in macros if r["field"] == "completionText"]
    lines.extend(["", "Key observations in this dataset:", "",
                  "- Astra has the highest introduction macro means on all four metrics. This describes stronger within-scenario overlap, not a quality ranking.",
                  f"- Completion LCS means are close ({min(completion_lcs):.4f}–{max(completion_lcs):.4f}), whereas semantic means differ more: " + ", ".join(f"{label} {macro_lookup[(label, 'completionText')]['semanticCosine']:.4f}" for label, *_ in COHORTS) + ".",
                  "- Similar lexical averages do not imply similar semantic averages. Read the original passages before attributing a pattern to templates, paraphrases, or required facts.", "",
                  "## Introduction versus completion across the eight scenarios", "",
                  "| Model | Introduction cosine > completion | Completion LCS > introduction |",
                  "|---|---:|---:|"])
    for label, *_ in COHORTS:
        lookup = {(r["scenarioId"], r["field"]): r for r in scenarios if r["model"] == label}
        intro_higher = sum(lookup[(s, FIELDS[0])]["semanticCosine"] > lookup[(s, FIELDS[1])]["semanticCosine"] for s in SCENARIOS)
        comp_higher = sum(lookup[(s, FIELDS[1])]["tokenLcsF1"] > lookup[(s, FIELDS[0])]["tokenLcsF1"] for s in SCENARIOS)
        lines.append(f"| {label} | {intro_higher}/8 | {comp_higher}/8 |")
    lines.extend(["", "## Lexical–semantic rank relationships", "",
                  "Spearman uses average ranks for ties. Pair-level compares pairs within a model/field; scenario-level compares just eight scenario means. These are distinct levels, not interchangeable evidence.", "",
                  "| Model | Field | Pair semantic–LCS Spearman | Scenario-mean semantic–LCS Spearman |",
                  "|---|---|---:|---:|"])
    for r in correlations:
        if r["lexicalMetric"] == "tokenLcsF1":
            lines.append(f"| {r['model']} | {r['field']} | {r['pairSpearman']:.4f} | {r['scenarioMeanSpearman']:.4f} |")
    lines.extend(["", "## Scenario detail", "",
                  "Every cell is a within-scenario mean; there are no cross-model text-pair scores in these tables."])
    for field in FIELDS:
        lines.extend(["", f"### {field}", "", "| Scenario | Model | Generations | Pairs | LCS | Word 3-gram | Cosine |",
                      "|---|---|---:|---:|---:|---:|---:|"])
        for scenario in SCENARIOS:
            for r in scenarios:
                if r["scenarioId"] == scenario and r["field"] == field:
                    lines.append(f"| {scenario} | {r['model']} | {r['generations']} | {r['pairs']} | {r['tokenLcsF1']:.4f} | {r['word3gramJaccard']:.4f} | {r['semanticCosine']:.4f} |")
    lines.extend(["", "## Cohorts and validation", "",
                  "| Model | Generations | Narrative pairs | Field rows | Audit pairs | Max wordpieces | Truncated texts |",
                  "|---|---:|---:|---:|---:|---:|---:|"])
    for r in checks:
        lines.append(f"| {r['label']} | 72 | {r['withinScenarioPairs']} | {r['fieldComparisons']} | 40 | {r['maximumObservedWordpieces']} | 0 |")
    lines.extend(["",
                  "- Sol keeps its original frozen first 206 physical lines and existing reports: unequal scenario counts, 72 starts, 62 logged completions. It is not relabeled as a 72-completion cohort.",
                  "- Terra/Astra use the first 216 physical lines. Luna uses the first 217 excluding only its known line-1 connection-error fallback. The extra automatically started quest is outside each fixed new cohort; nothing is deleted from raw logs.",
                  "- Each new cohort has nine generations per scenario, 72 starts/completions, empty initial continuity, and later summaries matching the preceding generation. Event POST arrival order can differ from generation order (Luna); coverage and summary chains are checked separately.",
                  "- Source prefix hashes, derived bytes, exact pair keys/texts/lexical scores, audit identities, and shared analyzer/model/runtime settings are verified before aggregation.",
                  "- MPNet: sentence-transformers/all-mpnet-base-v2; revision e8c3b32edf5434bc2275fc9bab85f82640a19130; 768 dimensions; CPU/float32; 384 wordpiece limit; offline load. No narrative API calls are made.",
                  "- Lexical uses NFKC/casefold/punctuation-to-space word tokenization. Semantic only collapses whitespace. Model settings match the original Sol analysis.",
                  "- Statistics here are calculated from persisted six-decimal pair CSV values; derived CSV summaries use nine decimals. Tiny last-digit correlation differences from per-model reports can arise because those reports use pre-serialization cosine values.", "",
                  "## Which files to read", "",
                  "- [Scenario detail](scenario_comparison.csv): 64 model/scenario/field rows, all four metrics.",
                  "- [Macro and secondary pooled means](model_macro_summary.csv): eight model/field rows. Pooled means are not the primary cross-model comparison.",
                  "- [Correlations](pair_correlations.csv): semantic versus each lexical metric at pair and scenario-mean levels.",
                  "- [Metric disagreement cases](metric_disagreement_cases.csv): five largest absolute semantic–LCS rank-percentile gaps per model/field, with original texts. Percentile = (N − descending average rank)/(N − 1). No quality cutoff or paraphrase label is assigned.",
                  "- [Cohort provenance](analysis_manifest.json) and [verification metadata](comparison_metadata.json).", "",
                  "Per-model reports and fixed audit samples:", ""])
    for c in manifest["cohorts"]:
        lex_dir, sem_dir = Path(c["lexicalDirectory"]), Path(c["semanticDirectory"])
        lines.append(f"- {c['label']}: [lexical report]({lex_dir / 'lexical_analysis_summary.md'}), [semantic report]({sem_dir / 'semantic_analysis_summary.md'}), [40-pair audit with texts and semantic scores]({sem_dir / 'hash_ranked_audit_sample_40_with_semantic.csv'}).")
    lines.extend(["", "## Limits and next interpretation step", "",
                  "These are four gameplay runs, not controlled identical-prompt replications. Scenario order and rolling previousStorySummary differ. Equal-scenario weighting corrects unequal scenario representation, not history differences or within-run dependence. Pairs reuse texts: 296/288 pair rows are not 296/288 independent experimental observations. No p-values, causal model superiority, quality/creativity ranking, or calibrated high-similarity thresholds are claimed.", "",
                  "Each model's 40-pair audit uses the same proportional SHA-256 ranking method/salt, but different actual pairs. The 40 disagreement field-cases are a separate diagnostic selection and may overlap audit samples. Reading these can explore required facts, paraphrasing, recurring phrases/templates, framing differences, and anomalous output; no qualitative labels have been assigned by this script. A single researcher's inspection is not independent human validation or ground truth.", "",
                  "Requested generation model IDs are recorded in the raw logs; a separate API-returned model ID was not retained. Luna's excluded API connection failure still belongs in any future reliability analysis.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT / "analysis_manifest.json")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    check_output_directory(args.output_dir.absolute())
    verify_environment()
    manifest = json.loads(args.manifest.read_text())
    require(len(manifest["cohorts"]) == 4, "Expected four cohorts")
    baseline = json.loads((BACKEND / "reports/semantic_frozen72_v1/analysis_metadata.json").read_text())
    scenarios, macros, correlations, gaps, checks = [], [], [], [], []
    for cohort, spec in zip(manifest["cohorts"], COHORTS):
        rows, check = load_cohort(cohort, spec, baseline)
        scenario_rows, macro_rows = summarize(cohort["label"], rows, cohort["scenarioGenerationCounts"])
        corr_rows, gap_rows = correlations_and_gaps(cohort["label"], rows, scenario_rows)
        scenarios.extend(scenario_rows)
        macros.extend(macro_rows)
        correlations.extend(corr_rows)
        gaps.extend(gap_rows)
        checks.append(check)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    tables = {"scenario_comparison.csv": scenarios, "model_macro_summary.csv": macros,
              "pair_correlations.csv": correlations, "metric_disagreement_cases.csv": gaps}
    for name, rows in tables.items():
        write_csv(output / name, rows)
    (output / "comparison_metadata.json").write_bytes(json_bytes({
        "version": "four-model-comparison-v1", "analyzerSha256": sha256(Path(__file__).read_bytes()),
        "runnerSha256": sha256((BACKEND / "run_model_analysis.py").read_bytes()),
        "manifestSha256": sha256(args.manifest.read_bytes()), "fields": list(FIELDS),
        "metrics": list(METRICS), "primaryAggregation": "equal mean of eight scenario pair means",
        "sourcePrecision": "six-decimal persisted pair scores", "qualityThresholds": None,
        "pValuesReported": False, "sharedSemanticSettings": {k: baseline[k] for k in SHARED_SETTINGS},
        "cohortChecks": checks,
        "outputs": {name: {"rows": len(rows), "sha256": sha256((output / name).read_bytes())} for name, rows in tables.items()},
    }))
    (output / "model_comparison.md").write_text(render_report(manifest, scenarios, macros, correlations, checks), encoding="utf-8")
    print(f"Verified 288 generations, 1160 narrative pairs, 2320 field rows, and 160 audit pairs.\n{output / 'model_comparison.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

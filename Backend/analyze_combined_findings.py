#!/usr/bin/env python3
"""Combine the formal frozen-72 lexical and semantic findings."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from analyze_lexical_similarity import (
    FROZEN_GENERATION_COUNT,
    FROZEN_PREFIX_SHA256,
    FROZEN_SCENARIO_GENERATION_COUNTS,
    LEXICAL_FIELDS,
)
from analyze_semantic_similarity import (
    FROZEN_AUDIT_PAIR_COUNT,
    FROZEN_LEXICAL_AUDIT_SHA256,
    FROZEN_LEXICAL_PAIRS_SHA256,
    SEMANTIC_METRIC_VERSION,
    _spearman,
)


BACKEND_DIRECTORY = Path(__file__).resolve().parent
LEXICAL_DIRECTORY = BACKEND_DIRECTORY / "reports" / "lexical_frozen72_v3"
SEMANTIC_DIRECTORY = BACKEND_DIRECTORY / "reports" / "semantic_frozen72_v1"
EXPERIMENT_DIRECTORY = (
    BACKEND_DIRECTORY / "reports" / "demo_2026-08-20_take01"
)
DEFAULT_OUTPUT_PATH = (
    BACKEND_DIRECTORY
    / "reports"
    / "combined_frozen72_v1"
    / "combined_findings.md"
)
LEXICAL_METADATA_PATH = LEXICAL_DIRECTORY / "analysis_metadata.json"
LEXICAL_SUMMARY_PATH = LEXICAL_DIRECTORY / "within_scenario_lexical_summary.csv"
LEXICAL_PAIRS_PATH = LEXICAL_DIRECTORY / "within_scenario_lexical_pairs.csv"
LEXICAL_AUDIT_PATH = LEXICAL_DIRECTORY / "hash_ranked_audit_sample_40.csv"
SEMANTIC_METADATA_PATH = SEMANTIC_DIRECTORY / "analysis_metadata.json"
SEMANTIC_SUMMARY_PATH = (
    SEMANTIC_DIRECTORY / "within_scenario_semantic_summary.csv"
)
SEMANTIC_PAIRS_PATH = SEMANTIC_DIRECTORY / "within_scenario_semantic_pairs.csv"
CORRELATIONS_PATH = SEMANTIC_DIRECTORY / "lexical_semantic_correlations.csv"
SEMANTIC_AUDIT_PATH = (
    SEMANTIC_DIRECTORY / "hash_ranked_audit_sample_40_with_semantic.csv"
)
GENERATIONS_PATH = EXPERIMENT_DIRECTORY / "generation_records.csv"
COMBINED_METHOD_VERSION = "combined-frozen72-v1"
EXPECTED_PAIRS = 296
EXPECTED_FIELD_ROWS = 592


# loads a saved analysis table with its existing column names
def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


# requires metadata to be a json object
def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"metadata is not an object: {path}")
    return value


# hashes a reference file without changing its contents
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


# reads a numeric result from a saved table
def number(row: dict[str, Any], field: str) -> float:
    return float(str(row[field]))


# reads boolean values saved as text in csv files
def truth(value: Any) -> bool:
    normalized = str(value).strip().casefold()
    if normalized not in {"true", "false"}:
        raise ValueError(f"expected Boolean text, received {value!r}")
    return normalized == "true"


# identifies a narrative pair within one scenario
def pair_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row["scenarioId"]),
        str(row["requestIdA"]),
        str(row["requestIdB"]),
    )


# adds the narrative field to a pair identity
def field_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (*pair_key(row), str(row["field"]))


# reconstructs the score independent identity used to select an audit pair
def expected_audit_hash(row: dict[str, Any]) -> str:
    raw = "|".join(
        (
            str(row["sampleSalt"]),
            str(row["scenarioId"]),
            str(row["requestIdA"]),
            str(row["requestIdB"]),
        )
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# uses average ranks for ties before comparing positions on different metric scales
def average_percentiles(
    rows: list[dict[str, Any]], metric: str
) -> dict[tuple[str, str, str, str], float]:
    """Return ascending average-rank percentiles; high scores approach one."""

    indexed = sorted(
        rows,
        key=lambda row: (number(row, metric), field_key(row)),
    )
    if not indexed:
        return {}
    denominator = max(1, len(indexed) - 1)
    results: dict[tuple[str, str, str, str], float] = {}
    start = 0
    while start < len(indexed):
        end = start + 1
        value = number(indexed[start], metric)
        while end < len(indexed) and number(indexed[end], metric) == value:
            end += 1
        average_zero_based_rank = (start + end - 1) / 2
        percentile = average_zero_based_rank / denominator
        for position in range(start, end):
            results[field_key(indexed[position])] = percentile
        start = end
    return results


# gives tied scenario values the same average descending rank
def descending_average_ranks(values: dict[str, float]) -> dict[str, float]:
    """Return one-based descending ranks with average ranks for exact ties."""

    indexed = sorted(values.items(), key=lambda item: (-item[1], item[0]))
    results: dict[str, float] = {}
    start = 0
    while start < len(indexed):
        end = start + 1
        while end < len(indexed) and indexed[end][1] == indexed[start][1]:
            end += 1
        average_rank = ((start + 1) + end) / 2
        for position in range(start, end):
            results[indexed[position][0]] = average_rank
        start = end
    return results


# requires the lexical and semantic files to describe the same frozen sol records
def validate_sources(
    lexical_metadata: dict[str, Any],
    semantic_metadata: dict[str, Any],
    lexical_rows: list[dict[str, str]],
    semantic_rows: list[dict[str, str]],
    lexical_audit: list[dict[str, str]],
    semantic_audit: list[dict[str, str]],
    generations: list[dict[str, str]],
) -> None:
    """Fail closed when the formal inputs no longer describe one dataset."""

    for label, metadata in (
        ("lexical", lexical_metadata),
        ("semantic", semantic_metadata),
    ):
        if metadata.get("inputPrefixSha256") != FROZEN_PREFIX_SHA256:
            raise ValueError(f"{label} input-prefix SHA-256 differs")
        if metadata.get("generationRecords") != FROZEN_GENERATION_COUNT:
            raise ValueError(f"{label} generation count differs")
    if semantic_metadata.get("semanticMetricVersion") != SEMANTIC_METRIC_VERSION:
        raise ValueError("semantic metric version differs")
    if sha256_file(LEXICAL_PAIRS_PATH) != FROZEN_LEXICAL_PAIRS_SHA256:
        raise ValueError("lexical-pair SHA-256 differs")
    if sha256_file(LEXICAL_AUDIT_PATH) != FROZEN_LEXICAL_AUDIT_SHA256:
        raise ValueError("lexical-audit SHA-256 differs")
    if len(lexical_rows) != EXPECTED_FIELD_ROWS:
        raise ValueError("lexical pair file does not contain 592 rows")
    if len(semantic_rows) != EXPECTED_FIELD_ROWS:
        raise ValueError("semantic pair file does not contain 592 rows")
    lexical_keys = [field_key(row) for row in lexical_rows]
    semantic_keys = [field_key(row) for row in semantic_rows]
    if lexical_keys != semantic_keys or len(set(semantic_keys)) != len(semantic_keys):
        raise ValueError("lexical/semantic keys or row order differ")

    pair_fields: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in semantic_rows:
        pair_fields[pair_key(row)].add(str(row["field"]))
    if len(pair_fields) != EXPECTED_PAIRS:
        raise ValueError("semantic rows do not contain 296 narrative pairs")
    if any(fields != set(LEXICAL_FIELDS) for fields in pair_fields.values()):
        raise ValueError("a narrative pair does not contain both fields")

    if len(lexical_audit) != FROZEN_AUDIT_PAIR_COUNT:
        raise ValueError("lexical audit does not contain 40 pairs")
    if len(semantic_audit) != FROZEN_AUDIT_PAIR_COUNT:
        raise ValueError("semantic audit does not contain 40 pairs")
    original_columns = list(lexical_audit[0])
    for original, enriched in zip(lexical_audit, semantic_audit):
        if any(
            str(original[column]) != str(enriched[column])
            for column in original_columns
        ):
            raise ValueError("semantic audit changed an original value or order")
        if original["selectionHash"] != expected_audit_hash(original):
            raise ValueError("audit selection hash is invalid")
        if pair_key(original) not in pair_fields:
            raise ValueError("audit pair is outside the pair population")

    if len(generations) != FROZEN_GENERATION_COUNT:
        raise ValueError("experiment generation file does not contain 72 rows")
    scenario_counts = Counter(row["scenarioId"] for row in generations)
    if dict(sorted(scenario_counts.items())) != FROZEN_SCENARIO_GENERATION_COUNTS:
        raise ValueError("experiment scenario counts differ")
    pair_request_ids = {
        row[side]
        for row in semantic_rows
        for side in ("requestIdA", "requestIdB")
    }
    generation_request_ids = {row["requestId"] for row in generations}
    if pair_request_ids != generation_request_ids:
        raise ValueError("experiment and semantic request IDs differ")


# collects lexical and semantic statistics while keeping each field separate
def build_profiles(
    lexical_summary: list[dict[str, str]],
    semantic_summary: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lexical_overall = {
        row["field"]: row
        for row in lexical_summary
        if row["aggregation"] == "overall"
    }
    semantic_overall = {
        row["field"]: row
        for row in semantic_summary
        if row["aggregation"] == "overall_pair_weighted"
    }
    if set(lexical_overall) != set(LEXICAL_FIELDS):
        raise ValueError("lexical overall rows are incomplete")
    if set(semantic_overall) != set(LEXICAL_FIELDS):
        raise ValueError("semantic overall rows are incomplete")
    overall: list[dict[str, Any]] = []
    for field in LEXICAL_FIELDS:
        lexical = lexical_overall[field]
        semantic = semantic_overall[field]
        overall.append(
            {
                "field": field,
                "pairs": int(semantic["comparisons"]),
                "lcsMean": number(lexical, "meanTokenLcsF1"),
                "lcsP90": number(lexical, "p90TokenLcsF1"),
                "word3Mean": number(lexical, "meanWord3gramJaccard"),
                "word3P90": number(lexical, "p90Word3gramJaccard"),
                "word3ZeroRate": number(lexical, "zeroWord3gramPairRate"),
                "semanticMean": number(semantic, "meanSemanticCosine"),
                "semanticMedian": number(semantic, "medianSemanticCosine"),
                "semanticP90": number(semantic, "p90SemanticCosine"),
                "semanticMacroMean": number(
                    semantic, "macroMeanOfScenarioMeans"
                ),
            }
        )

    lexical_scenarios = {
        (row["scenarioId"], row["field"]): row
        for row in lexical_summary
        if row["aggregation"] == "scenario"
    }
    semantic_scenarios = {
        (row["scenarioId"], row["field"]): row
        for row in semantic_summary
        if row["aggregation"] == "scenario"
    }
    if set(lexical_scenarios) != set(semantic_scenarios):
        raise ValueError("lexical and semantic scenario rows differ")
    if len(semantic_scenarios) != 8 * len(LEXICAL_FIELDS):
        raise ValueError("scenario summaries do not contain 16 field rows")

    profiles: list[dict[str, Any]] = []
    for scenario_id, field in sorted(semantic_scenarios):
        lexical = lexical_scenarios[(scenario_id, field)]
        semantic = semantic_scenarios[(scenario_id, field)]
        profiles.append(
            {
                "scenarioId": scenario_id,
                "field": field,
                "pairs": int(semantic["comparisons"]),
                "semanticMean": number(semantic, "meanSemanticCosine"),
                "lcsMean": number(lexical, "meanTokenLcsF1"),
                "word3Mean": number(lexical, "meanWord3gramJaccard"),
                "word1Mean": number(lexical, "meanWord1gramJaccard"),
            }
        )
    for field in LEXICAL_FIELDS:
        selected = [row for row in profiles if row["field"] == field]
        for metric in ("semanticMean", "lcsMean", "word3Mean"):
            ranks = descending_average_ranks(
                {row["scenarioId"]: row[metric] for row in selected}
            )
            for row in selected:
                row[f"{metric}Rank"] = ranks[row["scenarioId"]]
    return overall, profiles


# describes agreement across eight scenario averages without significance testing
def scenario_mean_associations(
    profiles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compare eight scenario means, giving every scenario equal weight."""

    results: list[dict[str, Any]] = []
    for field in LEXICAL_FIELDS:
        selected = sorted(
            (row for row in profiles if row["field"] == field),
            key=lambda row: row["scenarioId"],
        )
        semantic = [row["semanticMean"] for row in selected]
        for metric, role in (
            ("lcsMean", "tokenLcsF1"),
            ("word3Mean", "word3gramJaccard"),
            ("word1Mean", "word1gramJaccard"),
        ):
            results.append(
                {
                    "field": field,
                    "lexicalMetric": role,
                    "scenarios": len(selected),
                    "spearmanRho": _spearman(
                        semantic, [row[metric] for row in selected]
                    ),
                }
            )
    return results


# selects the largest relative metric disagreements for explanatory inspection
def rank_gap_cases(
    semantic_rows: list[dict[str, str]], limit: int = 3
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    results: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for field in LEXICAL_FIELDS:
        selected = [row for row in semantic_rows if row["field"] == field]
        semantic_percentiles = average_percentiles(selected, "semanticCosine")
        lcs_percentiles = average_percentiles(selected, "tokenLcsF1")
        cases: list[dict[str, Any]] = []
        for row in selected:
            key = field_key(row)
            semantic_percentile = semantic_percentiles[key]
            lcs_percentile = lcs_percentiles[key]
            cases.append(
                {
                    **row,
                    "semanticPercentile": semantic_percentile,
                    "lcsPercentile": lcs_percentile,
                    "semanticMinusLcs": semantic_percentile - lcs_percentile,
                    "lcsMinusSemantic": lcs_percentile - semantic_percentile,
                }
            )
        results[field] = {
            "semanticRankExceedsLcs": sorted(
                cases,
                key=lambda row: (-row["semanticMinusLcs"], field_key(row)),
            )[:limit],
            "lcsRankExceedsSemantic": sorted(
                cases,
                key=lambda row: (-row["lcsMinusSemantic"], field_key(row)),
            )[:limit],
        }
    return results


# summarises recorded operational context without inventing missing observations
def experiment_context(generations: list[dict[str, str]]) -> dict[str, Any]:
    completion_seconds = [
        number(row, "completionSeconds")
        for row in generations
        if row["completionSeconds"].strip()
    ]
    return {
        "generations": len(generations),
        "openai": sum(row["source"] == "openai" for row in generations),
        "fallbacks": sum(row["source"] == "fallback" for row in generations),
        "started": sum(truth(row["started"]) for row in generations),
        "completed": sum(truth(row["completed"]) for row in generations),
        "totalTokens": sum(int(row["totalTokens"]) for row in generations),
        "estimatedCost": sum(number(row, "estimatedCostUsd") for row in generations),
        "averageCompletionSeconds": statistics.fmean(completion_seconds),
    }


# escapes cell separators and line breaks for markdown tables
def md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


# formats short literal text for the markdown report
def code(value: Any) -> str:
    tick = chr(96)
    return f"{tick}{md(value)}{tick}"


# formats an available numerical score for display
def score(value: Any) -> str:
    return f"{float(value):.4f}"


# formats whole and tied ranks for display
def display_rank(value: Any) -> str:
    numeric = float(value)
    return str(int(numeric)) if numeric.is_integer() else f"{numeric:.1f}"


# shows the two request identifiers for a selected comparison
def pair_label(row: dict[str, Any]) -> str:
    left = str(row["requestIdA"])[:8]
    right = str(row["requestIdB"])[:8]
    return code(f"{left}… / {right}…")


# shows selected disagreement cases together with their original text
def render_gap_table(rows: Iterable[dict[str, Any]]) -> list[str]:
    lines = [
        "| Scenario | Pair | Semantic | Semantic pct. | LCS F1 | LCS pct. | Rank gap | Word-3 J | Titles |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        gap = abs(row["semanticPercentile"] - row["lcsPercentile"])
        lines.append(
            f"| {code(row['scenarioId'])} | {pair_label(row)} | "
            f"{score(row['semanticCosine'])} | "
            f"{score(row['semanticPercentile'])} | "
            f"{score(row['tokenLcsF1'])} | {score(row['lcsPercentile'])} | "
            f"{score(gap)} | {score(row['word3gramJaccard'])} | "
            f"{md(row['titleA'])} / {md(row['titleB'])} |"
        )
    return lines


# connects descriptive results to their interpretation limits
def render_report(
    lexical_metadata: dict[str, Any],
    semantic_metadata: dict[str, Any],
    overall: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    correlations: list[dict[str, str]],
    scenario_associations: list[dict[str, Any]],
    gaps: dict[str, dict[str, list[dict[str, Any]]]],
    audit: list[dict[str, str]],
    context: dict[str, Any],
    source_hashes: dict[str, str],
) -> str:
    profile_by_key = {
        (row["scenarioId"], row["field"]): row for row in profiles
    }
    scenarios = sorted({row["scenarioId"] for row in profiles})
    intro_semantic_higher = sum(
        profile_by_key[(scenario, "introduction")]["semanticMean"]
        > profile_by_key[(scenario, "completionText")]["semanticMean"]
        for scenario in scenarios
    )
    completion_lcs_higher = sum(
        profile_by_key[(scenario, "completionText")]["lcsMean"]
        > profile_by_key[(scenario, "introduction")]["lcsMean"]
        for scenario in scenarios
    )
    audit_counts = Counter(row["scenarioId"] for row in audit)
    lines = [
        "# Combined Lexical–Semantic Findings (Frozen 72)",
        "",
        "## Scope and status",
        "",
        f"- Method version: {code(COMBINED_METHOD_VERSION)}",
        "- Frozen input: first 206 physical JSONL lines",
        f"- Input SHA-256: {code(FROZEN_PREFIX_SHA256)}",
        f"- Generations: {context['generations']} across {len(scenarios)} scenarios",
        f"- Within-scenario narrative pairs: {EXPECTED_PAIRS}",
        f"- Field comparisons: {EXPECTED_FIELD_ROWS}",
        f"- Formal lexical method: {code('lexical-field-v3-word')}",
        f"- Formal semantic method: {code(semantic_metadata['semanticMetricVersion'])}",
        "- Legacy character-level SequenceMatcher bands are excluded.",
        "",
        "Only introduction and completionText are analyzed, separately. Titles "
        "remain visible for inspection but do not enter the lexical or semantic "
        "scores. All numerical summaries use all 296 pairs; the 40-pair audit "
        "does not estimate overall values.",
        "",
        "## Experiment context (not text similarity)",
        "",
        "| Generations | OpenAI | Fallbacks | Started | Completed | Completion rate | Mean completion time | Total tokens | Estimated cost |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| {context['generations']} | {context['openai']} | "
        f"{context['fallbacks']} | {context['started']} | "
        f"{context['completed']} | "
        f"{context['completed'] / context['started']:.1%} | "
        f"{context['averageCompletionSeconds']:.3f} s | "
        f"{context['totalTokens']:,} | "
        f"USD {context['estimatedCost']:.6f} |",
        "",
        "Lifecycle records provide started/completed outcomes but are excluded "
        "from every lexical and semantic calculation.",
        "",
        "## Formal measures",
        "",
        "- Token LCS F1: primary ordered lexical overlap.",
        "- Word 3-gram Jaccard: strict supplementary phrase overlap.",
        "- Word 1-gram Jaccard: descriptive vocabulary overlap in source tables.",
        "- MPNet cosine: primary whole-passage semantic similarity.",
        "- Spearman rho: primary cross-metric association; Pearson r: supplementary.",
        "- No score is a percentage, no metrics are averaged into one quality "
        "score, and no uncalibrated 80%/85% bands are used.",
        "",
        "## Overall within-scenario results",
        "",
        "| Field | Pairs | LCS mean | LCS P90 | Word-3 mean | Word-3 P90 | Word-3 zero | Semantic mean | Semantic median | Semantic P90 | Semantic macro mean |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in overall:
        lines.append(
            f"| {code(row['field'])} | {row['pairs']} | "
            f"{score(row['lcsMean'])} | {score(row['lcsP90'])} | "
            f"{score(row['word3Mean'])} | {score(row['word3P90'])} | "
            f"{row['word3ZeroRate']:.1%} | {score(row['semanticMean'])} | "
            f"{score(row['semanticMedian'])} | {score(row['semanticP90'])} | "
            f"{score(row['semanticMacroMean'])} |"
        )
    lines.extend(
        [
            "",
            "Completion has higher mean ordered lexical overlap, whereas "
            "introduction has higher mean semantic cosine. The score families "
            "measure different properties and do not share a common unit.",
            "",
            "## Scenario profiles",
        ]
    )
    for field in LEXICAL_FIELDS:
        lines.extend(
            [
                "",
                f"### {code(field)}",
                "",
                "| Scenario | Pairs | Semantic mean (rank) | LCS mean (rank) | Word-3 mean (rank) |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        selected = sorted(
            (row for row in profiles if row["field"] == field),
            key=lambda row: (row["semanticMeanRank"], row["scenarioId"]),
        )
        for row in selected:
            lines.append(
                f"| {code(row['scenarioId'])} | {row['pairs']} | "
                f"{score(row['semanticMean'])} "
                f"({display_rank(row['semanticMeanRank'])}) | "
                f"{score(row['lcsMean'])} "
                f"({display_rank(row['lcsMeanRank'])}) | "
                f"{score(row['word3Mean'])} "
                f"({display_rank(row['word3MeanRank'])}) |"
            )
    lines.extend(
        [
            "",
            "Ranks compare only the eight observed scenarios. Rank 1 means the "
            "highest observed mean for that metric, not the best narrative quality.",
            "",
            "## Cross-field findings",
            "",
            f"- Introduction semantic cosine exceeds completion in "
            f"{intro_semantic_higher}/{len(scenarios)} scenarios.",
            f"- Completion Token LCS F1 exceeds introduction in "
            f"{completion_lcs_higher}/{len(scenarios)} scenarios.",
        ]
    )
    for field in LEXICAL_FIELDS:
        selected = [row for row in profiles if row["field"] == field]
        semantic_highest = min(selected, key=lambda row: row["semanticMeanRank"])
        semantic_lowest = max(selected, key=lambda row: row["semanticMeanRank"])
        lcs_highest = min(selected, key=lambda row: row["lcsMeanRank"])
        lines.extend(
            [
                f"- {code(field)} semantic mean is highest for "
                f"{code(semantic_highest['scenarioId'])} "
                f"({score(semantic_highest['semanticMean'])}) and lowest for "
                f"{code(semantic_lowest['scenarioId'])} "
                f"({score(semantic_lowest['semanticMean'])}).",
                f"- {code(field)} LCS mean is highest for "
                f"{code(lcs_highest['scenarioId'])} "
                f"({score(lcs_highest['lcsMean'])}).",
            ]
        )
    lines.extend(
        [
            "",
            "## Lexical–semantic association",
            "",
            "| Field | Lexical measure | Pairs | Spearman rho | Pearson r |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in correlations:
        lines.append(
            f"| {code(row['field'])} | {code(row['lexicalMetric'])} | "
            f"{row['comparisons']} | {score(row['spearmanRho'])} | "
            f"{score(row['pearsonR'])} |"
        )
    lines.extend(
        [
            "",
            "All pair-level associations are positive, but none establishes "
            "equivalence between lexical and semantic measures. Pairs reuse "
            "narratives and may contain scenario-level differences, so ordinary "
            "independent-observation p-values are omitted.",
            "",
            "### Equal-scenario sensitivity",
            "",
            "This sensitivity calculation first reduces each field and scenario "
            "to one mean, then compares the rankings of the eight scenario means. "
            "It prevents scenarios with more pairs from receiving more weight, "
            "but n=8 is small, so the values remain descriptive.",
            "",
            "| Field | Lexical measure | Scenarios | Spearman rho |",
            "|---|---|---:|---:|",
        ]
    )
    for row in scenario_associations:
        lines.append(
            f"| {code(row['field'])} | {code(row['lexicalMetric'])} | "
            f"{row['scenarios']} | {score(row['spearmanRho'])} |"
        )
    lines.extend(
        [
            "",
            "Introduction scenario means show positive semantic–lexical rank "
            "agreement. Completion scenario means show little agreement between "
            "semantic cosine and LCS/Word-3, even though the corresponding "
            "pair-level associations are positive. The level of analysis therefore "
            "changes the conclusion, and both views are retained.",
            "",
            "## Pair-level rank-disagreement candidates",
            "",
            "Within each field, semantic cosine and Token LCS F1 are converted "
            "separately to average-rank percentiles across the same 296 pairs. "
            "Their gap surfaces cases where one measure ranks a pair much higher. "
            "This is dataset-relative case discovery, not a quality threshold and "
            "not automatic proof of paraphrasing or repetition.",
        ]
    )
    for field in LEXICAL_FIELDS:
        lines.extend(
            [
                "",
                f"### {code(field)}: semantic rank most exceeds LCS rank",
                "",
                *render_gap_table(gaps[field]["semanticRankExceedsLcs"]),
                "",
                f"### {code(field)}: LCS rank most exceeds semantic rank",
                "",
                *render_gap_table(gaps[field]["lcsRankExceedsSemantic"]),
            ]
        )

    allocation = ", ".join(
        f"{code(scenario)}={audit_counts[scenario]}"
        for scenario in sorted(audit_counts)
    )
    lines.extend(
        [
            "",
            "## Fixed 40-pair qualitative audit",
            "",
            f"Allocation: {allocation}.",
            "",
            "Within each scenario, every candidate receives "
            "SHA-256(20260820|scenarioId|requestIdA|requestIdB), is sorted by "
            "that hash, and the first allocated number is retained. Therefore "
            "\"same ranking positions\" means the same first hash-ranked positions, "
            "not the highest similarity scores. The semantic audit preserves all "
            "40 original rows, IDs, hashes, and order before appending cosine.",
            "",
            "The audit supports example inspection only. It is not human "
            "validation, does not calibrate thresholds, and does not calculate "
            "the reported means or correlations.",
            "",
            "## Defensible interpretation",
            "",
            "1. No exact normalized introduction or completion duplicates were "
            "observed, although ordered word and phrase overlap remains measurable.",
            "2. Introduction passages are closer in whole-passage semantic space "
            "on average, consistent with strong shared scenario content; this alone "
            "does not establish poor creativity.",
            "3. Completion passages have higher mean Token LCS F1 despite lower "
            "mean semantic cosine, which supports keeping wording and meaning separate.",
            "4. Positive but imperfect Spearman associations and the rank-gap cases "
            "show that neither score family subsumes the other.",
            "5. Scenario rankings describe these fixed outputs, not intrinsic "
            "properties of enemies or human judgments of quality.",
            "",
            "## Limits and next use",
            "",
            "- Same-scenario texts necessarily share enemies, locations, actions, "
            "and continuity facts.",
            "- MPNet is a general-English model, not a calibrated fantasy-creativity judge.",
            "- Pair rows are dependent because every narrative enters several pairs.",
            "- Without human-labelled ground truth, no high/review cutoff or "
            "classification accuracy is claimed.",
            "- MiniLM may later provide a model-sensitivity check; MPNet remains primary.",
            "",
            "The next analytical task is a transparent reading of the fixed "
            "40-pair audit and rank-gap cases, recording shared required facts, "
            "paraphrasing, repeated templates, different framing, and anomalies "
            "without turning these observations into unvalidated labels.",
            "",
            "## Reproducibility fingerprints",
            "",
            f"- Lexical analyzer SHA-256: "
            f"{code(lexical_metadata['analyzerSha256'])}",
            f"- Semantic analyzer SHA-256: "
            f"{code(semantic_metadata['analyzerSha256'])}",
        ]
    )
    for label, digest in source_hashes.items():
        lines.append(f"- {label} SHA-256: {code(digest)}")
    return "\n".join(lines) + "\n"


# reads the destination for the combined report
def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Combine frozen-72 experiment, lexical, and semantic findings."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


# checks frozen sources before writing a new combined findings report
def main() -> int:
    arguments = parse_arguments()
    required_paths = {
        "lexical summary": LEXICAL_SUMMARY_PATH,
        "lexical pairs": LEXICAL_PAIRS_PATH,
        "lexical audit": LEXICAL_AUDIT_PATH,
        "semantic summary": SEMANTIC_SUMMARY_PATH,
        "semantic pairs": SEMANTIC_PAIRS_PATH,
        "correlations": CORRELATIONS_PATH,
        "semantic audit": SEMANTIC_AUDIT_PATH,
        "generation records": GENERATIONS_PATH,
    }
    metadata_paths = (LEXICAL_METADATA_PATH, SEMANTIC_METADATA_PATH)
    missing = [
        str(path)
        for path in (*required_paths.values(), *metadata_paths)
        if not path.is_file()
    ]
    if missing:
        print("Required inputs are missing: " + ", ".join(missing))
        return 1

    lexical_metadata = read_json(LEXICAL_METADATA_PATH)
    semantic_metadata = read_json(SEMANTIC_METADATA_PATH)
    lexical_summary = read_csv(LEXICAL_SUMMARY_PATH)
    lexical_rows = read_csv(LEXICAL_PAIRS_PATH)
    lexical_audit = read_csv(LEXICAL_AUDIT_PATH)
    semantic_summary = read_csv(SEMANTIC_SUMMARY_PATH)
    semantic_rows = read_csv(SEMANTIC_PAIRS_PATH)
    correlations = read_csv(CORRELATIONS_PATH)
    semantic_audit = read_csv(SEMANTIC_AUDIT_PATH)
    generations = read_csv(GENERATIONS_PATH)
    try:
        validate_sources(
            lexical_metadata,
            semantic_metadata,
            lexical_rows,
            semantic_rows,
            lexical_audit,
            semantic_audit,
            generations,
        )
        overall, profiles = build_profiles(lexical_summary, semantic_summary)
    except ValueError as error:
        print(f"Combined analysis validation failed: {error}")
        return 1

    gaps = rank_gap_cases(semantic_rows)
    scenario_associations = scenario_mean_associations(profiles)
    context = experiment_context(generations)
    source_hashes = {
        label: sha256_file(path) for label, path in required_paths.items()
    }
    source_hashes["combined analyzer"] = sha256_file(Path(__file__).resolve())
    output_path = arguments.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_report(
            lexical_metadata,
            semantic_metadata,
            overall,
            profiles,
            correlations,
            scenario_associations,
            gaps,
            semantic_audit,
            context,
            source_hashes,
        ),
        encoding="utf-8",
    )
    print(
        f"Combined {len(generations)} generations, {EXPECTED_PAIRS} pairs, "
        f"and {len(semantic_rows)} field rows."
    )
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

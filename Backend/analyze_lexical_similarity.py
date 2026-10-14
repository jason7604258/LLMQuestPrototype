#!/usr/bin/env python3
"""Reproducible word-level lexical analysis for generated quest narratives.

The primary analysis compares different generations of the same exact scenario.
It is completely offline and uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

from analyze_experiments import get_record_type, normalize_text


BACKEND_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_INPUT_PATH = (
    BACKEND_DIRECTORY / "logs" / "demo_narrative_runs_2026-08-20_take01.jsonl"
)
DEFAULT_OUTPUT_DIRECTORY = (
    BACKEND_DIRECTORY / "reports" / "lexical_frozen72_v3"
)
DEFAULT_MAX_LINES = 206
DEFAULT_SAMPLE_SIZE = 40
DEFAULT_SAMPLE_SALT = "20260820"
DEFAULT_TOP_K = 10
FROZEN_PREFIX_SHA256 = (
    "e24f11761aa490997e4ef9d39a41ffc9da1888940510748237be369329e734ad"
)
FROZEN_GENERATION_COUNT = 72
FROZEN_SCENARIO_GENERATION_COUNTS = {
    "collect_mushroom_01": 8,
    "kill_torch_01": 9,
    "slay_caveborn_bear_01": 10,
    "slay_caveborn_lizard_01": 10,
    "slay_caveborn_snake_01": 10,
    "slay_caveborn_spider_01": 7,
    "slay_caveborn_turtle_01": 11,
    "slay_torch_boss_01": 7,
}
LEXICAL_FIELDS = ("introduction", "completionText")
METRIC_VERSION = "lexical-field-v3-word"
SAMPLE_METHOD = "proportional_stratified_sha256_rank"


def load_jsonl_prefix(
    path: Path,
    max_lines: int | None,
) -> tuple[list[dict[str, Any]], list[str], int, str]:
    """Load a physical-line prefix and return its SHA-256 for reproducibility."""

    records: list[dict[str, Any]] = []
    errors: list[str] = []
    digest = hashlib.sha256()
    lines_read = 0
    with path.open("rb") as source:
        for line_number, raw_line in enumerate(source, start=1):
            if max_lines is not None and line_number > max_lines:
                break
            lines_read += 1
            digest.update(raw_line)
            try:
                line = raw_line.decode("utf-8").strip()
            except UnicodeDecodeError as error:
                errors.append(
                    f"Line {line_number}: invalid UTF-8 ({error.reason})."
                )
                continue
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                errors.append(
                    f"Line {line_number}: invalid JSON ({error.msg})."
                )
                continue
            if not isinstance(value, dict):
                errors.append(
                    f"Line {line_number}: record is not a JSON object."
                )
                continue
            records.append(value)
    return records, errors, lines_read, digest.hexdigest()


def word_tokens(value: Any) -> list[str]:
    """Apply the shared text normalization and split it into word tokens."""

    return normalize_text(value).split()


def verify_prefix_hash(actual: str, expected: str | None) -> bool:
    """Fail closed when an expected input-prefix digest does not match."""

    if expected is None:
        return False
    normalized = expected.strip().casefold()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError("expected prefix SHA-256 must contain 64 hex characters")
    if actual.casefold() != normalized:
        raise ValueError(
            f"input prefix SHA-256 mismatch: expected {normalized}, got {actual}"
        )
    return True


def word_ngram_jaccard(
    left_tokens: list[str],
    right_tokens: list[str],
    n: int,
) -> float | None:
    """Return set Jaccard overlap for contiguous word n-grams.

    None means neither side contains an n-gram, so the metric is undefined.
    """

    if n < 1:
        raise ValueError("n must be at least 1")
    left_ngrams = {
        tuple(left_tokens[index : index + n])
        for index in range(len(left_tokens) - n + 1)
    }
    right_ngrams = {
        tuple(right_tokens[index : index + n])
        for index in range(len(right_tokens) - n + 1)
    }
    union = left_ngrams | right_ngrams
    if not union:
        return None
    return len(left_ngrams & right_ngrams) / len(union)


def token_lcs_length(left_tokens: list[str], right_tokens: list[str]) -> int:
    """Return longest common subsequence length using linear working memory."""

    # Keeping the shorter sequence in the columns limits memory use.
    if len(left_tokens) > len(right_tokens):
        left_tokens, right_tokens = right_tokens, left_tokens
    previous = [0] * (len(left_tokens) + 1)
    for right_token in right_tokens:
        current = [0]
        for index, left_token in enumerate(left_tokens, start=1):
            if left_token == right_token:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return previous[-1]


def token_lcs_f1(left_tokens: list[str], right_tokens: list[str]) -> float | None:
    """Return 2*LCS/(left length + right length), the token ROUGE-L-style F1."""

    total_length = len(left_tokens) + len(right_tokens)
    if total_length == 0:
        return None
    return 2 * token_lcs_length(left_tokens, right_tokens) / total_length


def _scenario_id(record: dict[str, Any]) -> str:
    scenario = record.get("scenario")
    if not isinstance(scenario, dict):
        return ""
    return str(scenario.get("scenarioId", "")).strip()


def _narrative_value(record: dict[str, Any], field: str) -> str:
    narrative = record.get("narrative")
    if not isinstance(narrative, dict):
        return ""
    value = narrative.get(field)
    return value if isinstance(value, str) else ""


def _record_sort_key(record: dict[str, Any]) -> tuple[str, str]:
    return (
        str(record.get("requestId", "")),
        str(record.get("timestampUtc", "")),
    )


def _rounded(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None


def build_within_scenario_field_rows(
    generations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Score both narrative fields for every unordered same-scenario pair."""

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in generations:
        scenario_id = _scenario_id(record)
        if scenario_id:
            groups[scenario_id].append(record)

    rows: list[dict[str, Any]] = []
    for scenario_id in sorted(groups):
        ordered = sorted(groups[scenario_id], key=_record_sort_key)
        for left, right in combinations(ordered, 2):
            for field in LEXICAL_FIELDS:
                left_text = _narrative_value(left, field)
                right_text = _narrative_value(right, field)
                left_tokens = word_tokens(left_text)
                right_tokens = word_tokens(right_text)
                # Missing text is not evidence of either repetition or diversity.
                if not left_tokens or not right_tokens:
                    continue
                lcs_length = token_lcs_length(left_tokens, right_tokens)
                rows.append(
                    {
                        "metricVersion": METRIC_VERSION,
                        "comparisonScope": "within_scenario",
                        "scenarioId": scenario_id,
                        "field": field,
                        "requestIdA": str(left.get("requestId", "")),
                        "requestIdB": str(right.get("requestId", "")),
                        "titleA": _narrative_value(left, "title"),
                        "titleB": _narrative_value(right, "title"),
                        "textA": left_text,
                        "textB": right_text,
                        "tokensA": len(left_tokens),
                        "tokensB": len(right_tokens),
                        "word1gramJaccard": word_ngram_jaccard(
                            left_tokens, right_tokens, 1
                        ),
                        "word3gramJaccard": word_ngram_jaccard(
                            left_tokens, right_tokens, 3
                        ),
                        "tokenLcsLength": lcs_length,
                        "tokenLcsF1": 2
                        * lcs_length
                        / (len(left_tokens) + len(right_tokens)),
                        "exactNormalizedText": left_tokens == right_tokens,
                    }
                )
    field_order = {field: index for index, field in enumerate(LEXICAL_FIELDS)}
    return sorted(
        rows,
        key=lambda row: (
            row["scenarioId"],
            row["requestIdA"],
            row["requestIdB"],
            field_order[row["field"]],
        ),
    )


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _metric_values(
    rows: list[dict[str, Any]], field: str
) -> list[float]:
    return [
        float(row[field])
        for row in rows
        if isinstance(row.get(field), (int, float))
        and not isinstance(row.get(field), bool)
    ]


def _add_metric_statistics(
    destination: dict[str, Any],
    rows: list[dict[str, Any]],
    source_field: str,
    output_name: str,
) -> None:
    values = _metric_values(rows, source_field)
    destination[f"valid{output_name}Pairs"] = len(values)
    destination[f"mean{output_name}"] = (
        _rounded(statistics.fmean(values)) if values else None
    )
    destination[f"median{output_name}"] = (
        _rounded(statistics.median(values)) if values else None
    )
    destination[f"p90{output_name}"] = _rounded(_percentile(values, 0.90))
    destination[f"maximum{output_name}"] = _rounded(max(values)) if values else None


def _summary_row(
    rows: list[dict[str, Any]],
    aggregation: str,
    field: str,
    scenario_id: str = "",
) -> dict[str, Any]:
    request_ids = {
        str(row[key])
        for row in rows
        for key in ("requestIdA", "requestIdB")
        if row.get(key)
    }
    exact_pairs = sum(bool(row["exactNormalizedText"]) for row in rows)
    trigram_values = _metric_values(rows, "word3gramJaccard")
    zero_trigram_pairs = sum(value == 0 for value in trigram_values)
    result: dict[str, Any] = {
        "metricVersion": METRIC_VERSION,
        "aggregation": aggregation,
        "comparisonScope": "within_scenario",
        "scenarioId": scenario_id,
        "field": field,
        "narrativesCompared": len(request_ids),
        "comparisons": len(rows),
    }
    _add_metric_statistics(
        result, rows, "word1gramJaccard", "Word1gramJaccard"
    )
    _add_metric_statistics(
        result, rows, "tokenLcsF1", "TokenLcsF1"
    )
    _add_metric_statistics(
        result, rows, "word3gramJaccard", "Word3gramJaccard"
    )
    result.update(
        {
            "zeroWord3gramPairs": zero_trigram_pairs,
            "zeroWord3gramPairRate": _rounded(
                _rate(zero_trigram_pairs, len(trigram_values))
            ),
            "exactPairs": exact_pairs,
            "exactPairRate": _rounded(_rate(exact_pairs, len(rows))),
        }
    )
    return result


def build_summary_rows(
    field_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build overall and exact-scenario descriptive summaries per field."""

    results: list[dict[str, Any]] = []
    for field in LEXICAL_FIELDS:
        selected = [row for row in field_rows if row["field"] == field]
        results.append(_summary_row(selected, "overall", field))

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in field_rows:
        grouped[(str(row["scenarioId"]), str(row["field"]))].append(row)
    field_order = {field: index for index, field in enumerate(LEXICAL_FIELDS)}
    for (scenario_id, field), selected in sorted(
        grouped.items(), key=lambda item: (item[0][0], field_order[item[0][1]])
    ):
        results.append(
            _summary_row(selected, "scenario", field, scenario_id)
        )
    return results


def build_top_rows(
    field_rows: list[dict[str, Any]], top_k: int
) -> list[dict[str, Any]]:
    """Return the top pairs for each field and metric without a fixed cutoff."""

    results: list[dict[str, Any]] = []
    metrics = (
        ("tokenLcsF1", "primary_ordered_overlap"),
        ("word3gramJaccard", "strict_phrase_overlap"),
        ("word1gramJaccard", "descriptive_vocabulary_overlap"),
    )
    for field in LEXICAL_FIELDS:
        field_selected = [row for row in field_rows if row["field"] == field]
        for metric, role in metrics:
            eligible = [
                row
                for row in field_selected
                if isinstance(row.get(metric), (int, float))
            ]
            eligible.sort(
                key=lambda row: (
                    -float(row[metric]),
                    row["scenarioId"],
                    row["requestIdA"],
                    row["requestIdB"],
                )
            )
            for rank, row in enumerate(eligible[:top_k], start=1):
                results.append(
                    {
                        "metricVersion": METRIC_VERSION,
                        "field": field,
                        "rankingMetric": metric,
                        "metricRole": role,
                        "rank": rank,
                        "rankingScore": row[metric],
                        "scenarioId": row["scenarioId"],
                        "requestIdA": row["requestIdA"],
                        "requestIdB": row["requestIdB"],
                        "titleA": row["titleA"],
                        "titleB": row["titleB"],
                        "word1gramJaccard": row["word1gramJaccard"],
                        "tokenLcsF1": row["tokenLcsF1"],
                        "word3gramJaccard": row["word3gramJaccard"],
                        "textA": row["textA"],
                        "textB": row["textB"],
                    }
                )
    return results


def _pair_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row["scenarioId"]),
        str(row["requestIdA"]),
        str(row["requestIdB"]),
    )


def _hamilton_allocation(
    group_sizes: dict[str, int], sample_size: int
) -> dict[str, int]:
    """Allocate a proportional integer sample by the largest-remainder rule."""

    total = sum(group_sizes.values())
    if sample_size < 0:
        raise ValueError("sample_size cannot be negative")
    if sample_size > total:
        raise ValueError("sample_size cannot exceed the pair population")
    if total == 0:
        return {key: 0 for key in group_sizes}
    quotas = {
        key: sample_size * size / total for key, size in group_sizes.items()
    }
    allocation = {key: math.floor(value) for key, value in quotas.items()}
    remaining = sample_size - sum(allocation.values())
    order = sorted(
        group_sizes,
        key=lambda key: (-(quotas[key] - allocation[key]), key),
    )
    for key in order[:remaining]:
        allocation[key] += 1
    return allocation


def _sample_hash(
    salt: str, scenario_id: str, request_id_a: str, request_id_b: str
) -> str:
    value = f"{salt}|{scenario_id}|{request_id_a}|{request_id_b}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_audit_sample(
    field_rows: list[dict[str, Any]],
    sample_size: int,
    salt: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Select pair IDs proportionally by scenario, independent of metric scores."""

    by_pair: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in field_rows:
        by_pair[_pair_key(row)][str(row["field"])] = row

    scenario_pairs: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for key in by_pair:
        scenario_pairs[key[0]].append(key)
    for keys in scenario_pairs.values():
        keys.sort()

    group_sizes = {key: len(value) for key, value in scenario_pairs.items()}
    allocation = _hamilton_allocation(group_sizes, sample_size)
    selected: list[tuple[str, str, str, str]] = []
    for scenario_id in sorted(scenario_pairs):
        ranked = sorted(
            scenario_pairs[scenario_id],
            key=lambda key: (
                _sample_hash(salt, key[0], key[1], key[2]),
                key,
            ),
        )
        for key in ranked[: allocation[scenario_id]]:
            selected.append(
                (
                    key[0],
                    key[1],
                    key[2],
                    _sample_hash(salt, key[0], key[1], key[2]),
                )
            )

    results: list[dict[str, Any]] = []
    for sample_number, (scenario_id, request_a, request_b, hash_value) in enumerate(
        selected, start=1
    ):
        fields = by_pair[(scenario_id, request_a, request_b)]
        introduction = fields.get("introduction", {})
        completion = fields.get("completionText", {})
        metadata = introduction or completion
        results.append(
            {
                "metricVersion": METRIC_VERSION,
                "sampleMethod": SAMPLE_METHOD,
                "sampleSalt": salt,
                "sampleNumber": sample_number,
                "selectionHash": hash_value,
                "scenarioId": scenario_id,
                "scenarioPairPopulation": group_sizes[scenario_id],
                "scenarioSampleSize": allocation[scenario_id],
                "requestIdA": request_a,
                "requestIdB": request_b,
                "titleA": metadata.get("titleA", ""),
                "titleB": metadata.get("titleB", ""),
                "introductionWord1gramJaccard": introduction.get(
                    "word1gramJaccard"
                ),
                "introductionTokenLcsF1": introduction.get("tokenLcsF1"),
                "introductionWord3gramJaccard": introduction.get(
                    "word3gramJaccard"
                ),
                "introductionA": introduction.get("textA", ""),
                "introductionB": introduction.get("textB", ""),
                "completionWord1gramJaccard": completion.get(
                    "word1gramJaccard"
                ),
                "completionTokenLcsF1": completion.get("tokenLcsF1"),
                "completionWord3gramJaccard": completion.get(
                    "word3gramJaccard"
                ),
                "completionA": completion.get("textA", ""),
                "completionB": completion.get("textB", ""),
            }
        )
    return results, allocation


def _format_number(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.4f}"


def _format_rate(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.1%}"


def render_summary(
    metadata: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    top_rows: list[dict[str, Any]],
) -> str:
    """Render a compact, dissertation-auditable Markdown summary."""

    lines = [
        f"# Word-level Lexical Analysis ({metadata['generationRecords']} generations)",
        "",
        "## Dataset",
        "",
        f"- Input: `{metadata['inputPath']}`",
        f"- Physical-line prefix: {metadata['linesRead']}",
        f"- Prefix SHA-256: `{metadata['inputPrefixSha256']}`",
        f"- Expected prefix SHA-256: "
        f"`{metadata['expectedInputPrefixSha256'] or 'not supplied'}`",
        f"- Prefix hash verified: {str(metadata['inputPrefixHashVerified']).lower()}",
        f"- Parsed JSON-object records: {metadata['parsedJsonObjectRecords']}",
        f"- Malformed/non-object records skipped: {metadata['malformedRecords']}",
        f"- Generation records: {metadata['generationRecords']}",
        f"- Within-scenario narrative pairs: {metadata['withinScenarioPairs']}",
        f"- Field-level comparisons: {metadata['fieldComparisons']}",
        "",
        "## Method",
        "",
        "Text is normalized with Unicode NFKC and case folding; runs of non-word "
        "characters and underscores are replaced with spaces, whitespace is "
        "collapsed, and the result is split into word tokens. `introduction` and "
        "`completionText` are compared separately. Only pairs with the same exact "
        "non-empty `scenarioId` enter this primary analysis.",
        "",
        "- **Symmetric Token LCS F1 (ROUGE-L-style)** is the primary ordered "
        "overlap metric: `2 × LCS length / (tokens A + tokens B)`. LCS preserves "
        "relative word order but allows gaps; it is not a standard ROUGE score "
        "with reference/candidate direction.",
        "- **Word 3-gram Jaccard** compares sets of unique contiguous word triples. "
        "It is a strict supplementary phrase-overlap metric and ignores frequency.",
        "  It is undefined if neither text contains a word triple; zero-rate "
        "denominators include only pairs with a defined 3-gram score.",
        "- **Word 1-gram Jaccard** compares sets of unique words. It describes "
        "vocabulary overlap but ignores word order and frequency.",
        "- Numbers are retained. No stopwords, stemming, or lemmatization are used, "
        "and no uncalibrated high/review thresholds are assigned.",
        "- P90 uses linear interpolation at position `(n - 1) × 0.90`.",
        "- Magnitudes are not directly comparable between the three metrics. "
        "Completion texts are also shorter and more constrained than introductions.",
        "- Scores describe wording overlap, not semantic similarity or narrative quality.",
        "",
        "## Overall within-scenario results (pooled pair-weighted)",
        "",
        "| Field | Pairs | Word-1 J mean | Word-1 J P90 | Token LCS F1 mean | Token LCS F1 P90 | Word-3 J mean | Word-3 J P90 | Word-3 zero | Exact |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    overall = [row for row in summary_rows if row["aggregation"] == "overall"]
    for row in overall:
        lines.append(
            f"| `{row['field']}` | {row['comparisons']} | "
            f"{_format_number(row['meanWord1gramJaccard'])} | "
            f"{_format_number(row['p90Word1gramJaccard'])} | "
            f"{_format_number(row['meanTokenLcsF1'])} | "
            f"{_format_number(row['p90TokenLcsF1'])} | "
            f"{_format_number(row['meanWord3gramJaccard'])} | "
            f"{_format_number(row['p90Word3gramJaccard'])} | "
            f"{row['zeroWord3gramPairs']} "
            f"({_format_rate(row['zeroWord3gramPairRate'])}) | "
            f"{row['exactPairs']} |"
        )

    lines.extend(
        [
            "",
            "## Per-scenario results",
            "",
            "| Scenario | Field | Pairs | Word-1 J mean | Token LCS F1 mean | Token LCS F1 P90 | Token LCS F1 max | Word-3 J mean | Word-3 zero |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in summary_rows:
        if row["aggregation"] != "scenario":
            continue
        lines.append(
            f"| `{row['scenarioId']}` | `{row['field']}` | "
            f"{row['comparisons']} | "
            f"{_format_number(row['meanWord1gramJaccard'])} | "
            f"{_format_number(row['meanTokenLcsF1'])} | "
            f"{_format_number(row['p90TokenLcsF1'])} | "
            f"{_format_number(row['maximumTokenLcsF1'])} | "
            f"{_format_number(row['meanWord3gramJaccard'])} | "
            f"{_format_rate(row['zeroWord3gramPairRate'])} |"
        )

    lines.extend(
        [
            "",
            "## Highest Token LCS F1 pairs",
            "",
            "| Field | Rank | Score | Scenario | Title A | Title B | Request A | Request B |",
            "|---|---:|---:|---|---|---|---|---|",
        ]
    )
    for row in top_rows:
        if row["rankingMetric"] != "tokenLcsF1" or row["rank"] > 5:
            continue
        title_a = str(row["titleA"]).replace("|", "\\|")
        title_b = str(row["titleB"]).replace("|", "\\|")
        lines.append(
            f"| `{row['field']}` | {row['rank']} | "
            f"{_format_number(row['rankingScore'])} | "
            f"`{row['scenarioId']}` | {title_a} | {title_b} | "
            f"`{row['requestIdA']}` | `{row['requestIdB']}` |"
        )

    lines.extend(
        [
            "",
            "## Reproducible audit sample",
            "",
            f"The audit CSV contains {metadata['sampleSize']} unique narrative pairs. "
            f"It uses proportional scenario strata and deterministic SHA-256 ranking "
            f"with fixed salt `{metadata['sampleSalt']}`. Selection did not use "
            "similarity scores or score bands.",
            "",
            f"The {metadata['sampleSize']} rows are a qualitative inspection set, "
            "**not** human validation. "
            f"All {metadata['withinScenarioPairs']} pairs are used for the numerical "
            "analysis. Pair scores are not "
            "statistically independent because one narrative participates in multiple "
            "pairs; the report therefore presents descriptive statistics only.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: _rounded(value) if isinstance(value, float) else value
                    for key, value in row.items()
                }
            )


def write_outputs(
    output_directory: Path,
    metadata: dict[str, Any],
    field_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    top_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
) -> list[Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    metadata_path = output_directory / "analysis_metadata.json"
    pairs_path = output_directory / "within_scenario_lexical_pairs.csv"
    summary_csv_path = output_directory / "within_scenario_lexical_summary.csv"
    top_path = output_directory / "top_lexical_pairs.csv"
    audit_path = output_directory / f"hash_ranked_audit_sample_{len(audit_rows)}.csv"
    summary_md_path = output_directory / "lexical_analysis_summary.md"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_csv(pairs_path, field_rows)
    write_csv(summary_csv_path, summary_rows)
    write_csv(top_path, top_rows)
    write_csv(audit_path, audit_rows)
    summary_md_path.write_text(
        render_summary(metadata, summary_rows, top_rows), encoding="utf-8"
    )
    return [
        summary_md_path,
        metadata_path,
        pairs_path,
        summary_csv_path,
        top_path,
        audit_path,
    ]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze word-level lexical overlap within exact scenarios, offline."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIRECTORY
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=DEFAULT_MAX_LINES,
        help=(
            "Read only this many physical input lines; use 0 for all lines "
            f"(default: {DEFAULT_MAX_LINES}, the frozen-72 prefix)."
        ),
    )
    parser.add_argument(
        "--expected-prefix-sha256",
        help=(
            "Fail unless the analyzed physical-line prefix has this SHA-256. "
            "The known frozen hash is applied automatically for the default "
            "input and 206-line prefix."
        ),
    )
    parser.add_argument(
        "--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE
    )
    parser.add_argument(
        "--sample-salt",
        "--sample-seed",
        dest="sample_salt",
        default=DEFAULT_SAMPLE_SALT,
        help=(
            "Fixed salt for deterministic SHA-256 pair ranking "
            f"(default: {DEFAULT_SAMPLE_SALT})."
        ),
    )
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    arguments = parser.parse_args()
    if arguments.max_lines < 0:
        parser.error("--max-lines cannot be negative")
    if arguments.sample_size < 0:
        parser.error("--sample-size cannot be negative")
    if arguments.top_k < 0:
        parser.error("--top-k cannot be negative")
    return arguments


def main() -> int:
    arguments = parse_arguments()
    input_path = arguments.input.expanduser().resolve()
    output_directory = arguments.output_dir.expanduser().resolve()
    if not input_path.is_file():
        print(f"Input log does not exist: {input_path}")
        return 1
    max_lines = arguments.max_lines or None
    records, errors, lines_read, prefix_hash = load_jsonl_prefix(
        input_path, max_lines
    )
    if max_lines is not None and lines_read != max_lines:
        print(
            f"Requested {max_lines} physical lines but input contains only "
            f"{lines_read}; analysis stopped."
        )
        return 1
    default_frozen_request = (
        input_path == DEFAULT_INPUT_PATH.resolve()
        and arguments.max_lines == DEFAULT_MAX_LINES
    )
    expected_prefix_hash = arguments.expected_prefix_sha256
    if expected_prefix_hash is None and default_frozen_request:
        expected_prefix_hash = FROZEN_PREFIX_SHA256
    try:
        prefix_hash_verified = verify_prefix_hash(
            prefix_hash, expected_prefix_hash
        )
    except ValueError as error:
        print(f"Input verification failed: {error}")
        return 1

    generations = [
        record for record in records if get_record_type(record) == "generation"
    ]
    field_rows = build_within_scenario_field_rows(generations)
    pair_keys = {_pair_key(row) for row in field_rows}
    if arguments.sample_size > len(pair_keys):
        print(
            f"Sample size {arguments.sample_size} exceeds the "
            f"{len(pair_keys)} eligible narrative pairs."
        )
        return 1
    summary_rows = build_summary_rows(field_rows)
    top_rows = build_top_rows(field_rows, arguments.top_k)
    audit_rows, allocation = build_audit_sample(
        field_rows, arguments.sample_size, str(arguments.sample_salt)
    )

    scenario_generation_counts: dict[str, int] = defaultdict(int)
    for record in generations:
        scenario_generation_counts[_scenario_id(record)] += 1
    if default_frozen_request and prefix_hash_verified:
        actual_scenario_counts = dict(sorted(scenario_generation_counts.items()))
        if (
            len(generations) != FROZEN_GENERATION_COUNT
            or actual_scenario_counts != FROZEN_SCENARIO_GENERATION_COUNTS
        ):
            print(
                "Frozen input parsed with unexpected generation/scenario counts; "
                "analysis stopped."
            )
            return 1
    scenario_pair_counts: dict[str, int] = defaultdict(int)
    for scenario_id, _, _ in pair_keys:
        scenario_pair_counts[scenario_id] += 1
    analyzer_path = Path(__file__).resolve()
    normalization_dependency = BACKEND_DIRECTORY / "analyze_experiments.py"
    metadata = {
        "metricVersion": METRIC_VERSION,
        "analyzerSha256": hashlib.sha256(analyzer_path.read_bytes()).hexdigest(),
        "normalizationDependencySha256": hashlib.sha256(
            normalization_dependency.read_bytes()
        ).hexdigest(),
        "inputPath": str(input_path),
        "requestedMaxPhysicalLines": arguments.max_lines,
        "linesRead": lines_read,
        "inputPrefixSha256": prefix_hash,
        "expectedInputPrefixSha256": expected_prefix_hash,
        "inputPrefixHashVerified": prefix_hash_verified,
        "parsedJsonObjectRecords": len(records),
        "malformedRecords": len(errors),
        "loadErrors": errors,
        "generationRecords": len(generations),
        "scenarioGenerationCounts": dict(sorted(scenario_generation_counts.items())),
        "withinScenarioPairs": len(pair_keys),
        "scenarioPairCounts": dict(sorted(scenario_pair_counts.items())),
        "fieldComparisons": len(field_rows),
        "fields": list(LEXICAL_FIELDS),
        "normalization": (
            "Unicode NFKC + casefold + replace runs of non-word characters "
            "and underscores with spaces + whitespace collapse"
        ),
        "tokenization": (
            "Whitespace split after normalization; numbers retained; no stopword "
            "removal, stemming, or lemmatization"
        ),
        "p90Method": "linear interpolation at position (n - 1) * 0.90",
        "primaryMetric": "tokenLcsF1",
        "supplementaryStrictPhraseMetric": "word3gramJaccard",
        "descriptiveVocabularyMetric": "word1gramJaccard",
        "sampleMethod": SAMPLE_METHOD,
        "sampleSalt": str(arguments.sample_salt),
        "sampleSize": len(audit_rows),
        "sampleAllocation": dict(sorted(allocation.items())),
        "topK": arguments.top_k,
    }
    paths = write_outputs(
        output_directory,
        metadata,
        field_rows,
        summary_rows,
        top_rows,
        audit_rows,
    )
    print(
        f"Analyzed {len(generations)} generations, {len(pair_keys)} "
        f"within-scenario narrative pairs, and {len(field_rows)} field rows."
    )
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

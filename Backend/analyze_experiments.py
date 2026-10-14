#!/usr/bin/env python3
"""analyzes story generation and gameplay jsonl records offline

this script uses only the python standard library and never contacts openai
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable


# default file locations and field-level lexical similarity limits
BACKEND_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_INPUT_PATH = BACKEND_DIRECTORY / "logs" / "narrative_runs.jsonl"
DEFAULT_OUTPUT_DIRECTORY = BACKEND_DIRECTORY / "reports"
LEXICAL_METRIC_VERSION = "lexical-field-v2"
LEXICAL_FIELDS = ("introduction", "completionText")
LEXICAL_FIELD_ORDER = {field: index for index, field in enumerate(LEXICAL_FIELDS)}
DEFAULT_REVIEW_THRESHOLD = 0.80
DEFAULT_SIMILARITY_THRESHOLD = 0.85


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """loads valid json objects and reports bad lines"""

    # valid records and readable errors are returned separately
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    with path.open("r", encoding="utf-8") as source:
        # each nonblank line must contain one json object
        for line_number, raw_line in enumerate(source, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                errors.append(f"Line {line_number}: invalid JSON ({error.msg}).")
                continue
            if not isinstance(value, dict):
                errors.append(f"Line {line_number}: record is not a JSON object.")
                continue
            records.append(value)
    return records, errors


def get_record_type(record: dict[str, Any]) -> str:
    """returns the saved type or finds older generation records"""

    # new records save their type directly
    explicit_type = record.get("recordType")
    if isinstance(explicit_type, str):
        return explicit_type
    # older generation records can be found by their story and scenario data
    if isinstance(record.get("narrative"), dict) and isinstance(
        record.get("scenario"), dict
    ):
        return "generation"
    return "unknown"


def normalize_text(value: Any) -> str:
    """cleans text for exact and word based comparisons"""

    # joins letter forms case punctuation and repeated spaces
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def normalized_narrative_field(record: dict[str, Any], field: str) -> str:
    """returns one normalized narrative field or empty text"""

    narrative = record.get("narrative")
    if not isinstance(narrative, dict):
        return ""
    value = narrative.get(field)
    if not isinstance(value, str):
        return ""
    return normalize_text(value)


def lexical_sequence_similarity(left_text: str, right_text: str) -> float:
    """returns a symmetric normalized character-sequence similarity"""

    # autojunk is disabled because introductions commonly exceed 200 characters
    # and frequent letters should not disappear from a narrative wording metric
    forward = SequenceMatcher(
        None,
        left_text,
        right_text,
        autojunk=False,
    ).ratio()
    reverse = SequenceMatcher(
        None,
        right_text,
        left_text,
        autojunk=False,
    ).ratio()
    # averaging both directions prevents input/log order from changing the score
    return (forward + reverse) / 2


def _number(value: Any) -> float | None:
    """returns a number as float or none for a bad value"""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _mean(values: Iterable[float | None]) -> float | None:
    """returns the mean of known values or none"""

    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return None
    return statistics.fmean(valid_values)


def _rate(numerator: int, denominator: int) -> float | None:
    """returns a rate or none when there is no total"""

    if denominator == 0:
        return None
    return numerator / denominator


def _scenario(record: dict[str, Any]) -> dict[str, Any]:
    """returns scenario data or an empty object"""

    value = record.get("scenario")
    return value if isinstance(value, dict) else {}


def _continuity_provided(record: dict[str, Any]) -> bool:
    """checks whether a request included earlier story context"""

    continuity = record.get("continuity")
    return bool(
        isinstance(continuity, dict) and continuity.get("wasProvided") is True
    )


def _backend_accepted(record: dict[str, Any]) -> bool | None:
    """returns the known backend validation result"""

    validation = record.get("validation")
    if not isinstance(validation, dict):
        return None
    value = validation.get("returnedNarrativeAccepted")
    return value if isinstance(value, bool) else None


def _unity_accepted(event: dict[str, Any]) -> bool | None:
    """returns the known unity validation result"""

    validation = event.get("unityValidation")
    if not isinstance(validation, dict):
        return None
    value = validation.get("backendNarrativeAccepted")
    return value if isinstance(value, bool) else None


def _narrative_value(record: dict[str, Any], field: str) -> str:
    """returns one original narrative string or empty text"""

    narrative = record.get("narrative")
    if not isinstance(narrative, dict):
        return ""
    value = narrative.get(field)
    return value if isinstance(value, str) else ""


def _similarity_band(
    similarity: float,
    exact: bool,
    review_threshold: float,
    high_threshold: float,
) -> str:
    """classifies one field comparison using inclusive thresholds"""

    if exact:
        return "exact"
    if similarity >= high_threshold:
        return "high"
    if similarity >= review_threshold:
        return "review"
    return "unflagged"


def _pair_scope(left_scenario_id: str, right_scenario_id: str) -> str:
    """returns whether a comparison is within across or missing a scenario"""

    if not left_scenario_id or not right_scenario_id:
        return "unknown_scenario"
    if left_scenario_id == right_scenario_id:
        return "within_scenario"
    return "cross_scenario"


def build_field_similarity_pairs(
    generations: list[dict[str, Any]],
    high_threshold: float,
    review_threshold: float,
) -> list[dict[str, Any]]:
    """compares introduction and completion text separately for every pair"""

    if not 0 <= review_threshold <= high_threshold <= 1:
        raise ValueError(
            "thresholds must satisfy 0 <= review_threshold <= "
            "high_threshold <= 1"
        )

    # Stable ordering makes the output independent of the JSONL record order.
    prepared = sorted(
        generations,
        key=lambda record: (
            str(_scenario(record).get("scenarioId", "")),
            str(record.get("requestId", "")),
            str(record.get("timestampUtc", "")),
        ),
    )
    pairs: list[dict[str, Any]] = []
    for left_index, left in enumerate(prepared):
        for right in prepared[left_index + 1 :]:
            left_scenario_id = str(_scenario(left).get("scenarioId", "")).strip()
            right_scenario_id = str(_scenario(right).get("scenarioId", "")).strip()
            scope = _pair_scope(left_scenario_id, right_scenario_id)
            for field in LEXICAL_FIELDS:
                left_text = normalized_narrative_field(left, field)
                right_text = normalized_narrative_field(right, field)
                # A missing field is not evidence of either similarity or diversity.
                if not left_text or not right_text:
                    continue
                exact = left_text == right_text
                similarity = round(
                    lexical_sequence_similarity(left_text, right_text),
                    6,
                )
                band = _similarity_band(
                    similarity,
                    exact,
                    review_threshold,
                    high_threshold,
                )
                pairs.append(
                    {
                        "metricVersion": LEXICAL_METRIC_VERSION,
                        "reviewThreshold": review_threshold,
                        "highThreshold": high_threshold,
                        "field": field,
                        "comparisonScope": scope,
                        "scenarioIdA": left_scenario_id,
                        "scenarioIdB": right_scenario_id,
                        "requestIdA": str(left.get("requestId", "")),
                        "requestIdB": str(right.get("requestId", "")),
                        "sourceA": str(left.get("source", "")),
                        "sourceB": str(right.get("source", "")),
                        "modelA": str(left.get("model", "")),
                        "modelB": str(right.get("model", "")),
                        "promptVersionA": str(left.get("promptVersion", "")),
                        "promptVersionB": str(right.get("promptVersion", "")),
                        "titleA": _narrative_value(left, "title"),
                        "titleB": _narrative_value(right, "title"),
                        "textA": _narrative_value(left, field),
                        "textB": _narrative_value(right, field),
                        "similarity": similarity,
                        "similarityBand": band,
                        "exactNormalizedText": exact,
                    }
                )
    return sorted(
        pairs,
        key=lambda item: (
            item["comparisonScope"] != "within_scenario",
            item["comparisonScope"],
            LEXICAL_FIELD_ORDER[item["field"]],
            -item["similarity"],
            item["scenarioIdA"],
            item["scenarioIdB"],
            item["requestIdA"],
            item["requestIdB"],
        ),
    )


def find_similar_narratives(
    generations: list[dict[str, Any]],
    threshold: float,
    review_threshold: float = DEFAULT_REVIEW_THRESHOLD,
) -> list[dict[str, Any]]:
    """returns review high and exact field-level comparisons"""

    return [
        pair
        for pair in build_field_similarity_pairs(
            generations,
            threshold,
            review_threshold,
        )
        if pair["similarityBand"] != "unflagged"
    ]


def _percentile(values: list[float], quantile: float) -> float | None:
    """returns a linearly interpolated percentile or none for no values"""

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


def _similarity_summary_row(
    rows: list[dict[str, Any]],
    aggregation: str,
    comparison_scope: str,
    field: str,
    review_threshold: float,
    high_threshold: float,
    scenario_id_a: str = "",
    scenario_id_b: str = "",
) -> dict[str, Any]:
    """summarizes one explicitly identified group of field comparisons"""

    scores = [float(row["similarity"]) for row in rows]
    exact_pairs = sum(row["similarityBand"] == "exact" for row in rows)
    review_pairs = sum(row["similarityBand"] == "review" for row in rows)
    high_non_exact_pairs = sum(row["similarityBand"] == "high" for row in rows)
    high_or_exact_pairs = exact_pairs + high_non_exact_pairs
    narrative_ids = {
        str(row[key])
        for row in rows
        for key in ("requestIdA", "requestIdB")
        if row.get(key)
    }
    comparisons = len(rows)
    return {
        "metricVersion": LEXICAL_METRIC_VERSION,
        "reviewThreshold": review_threshold,
        "highThreshold": high_threshold,
        "aggregation": aggregation,
        "comparisonScope": comparison_scope,
        "scenarioIdA": scenario_id_a,
        "scenarioIdB": scenario_id_b,
        "field": field,
        "narrativesCompared": len(narrative_ids),
        "comparisons": comparisons,
        "meanSimilarity": round(statistics.fmean(scores), 6) if scores else None,
        "medianSimilarity": round(statistics.median(scores), 6) if scores else None,
        "p90Similarity": (
            round(_percentile(scores, 0.90), 6) if scores else None
        ),
        "maximumSimilarity": round(max(scores), 6) if scores else None,
        "exactPairs": exact_pairs,
        "exactPairRate": _rate(exact_pairs, comparisons),
        "reviewPairs": review_pairs,
        "reviewPairRate": _rate(review_pairs, comparisons),
        "highNonExactPairs": high_non_exact_pairs,
        "highNonExactPairRate": _rate(high_non_exact_pairs, comparisons),
        "highOrExactPairs": high_or_exact_pairs,
        "highOrExactPairRate": _rate(high_or_exact_pairs, comparisons),
    }


def build_field_similarity_summary(
    pairs: list[dict[str, Any]],
    review_threshold: float = DEFAULT_REVIEW_THRESHOLD,
    high_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> list[dict[str, Any]]:
    """builds overall within-scenario and cross-scenario summary rows"""

    rows: list[dict[str, Any]] = []
    # Always emit these four overall rows so an empty comparison set is explicit.
    for scope in ("within_scenario", "cross_scenario"):
        for field in LEXICAL_FIELDS:
            selected = [
                pair
                for pair in pairs
                if pair["comparisonScope"] == scope and pair["field"] == field
            ]
            rows.append(
                _similarity_summary_row(
                    selected,
                    "overall",
                    scope,
                    field,
                    review_threshold,
                    high_threshold,
                )
            )

    within_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    cross_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    unknown_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pairs:
        scope = pair["comparisonScope"]
        field = pair["field"]
        if scope == "within_scenario":
            within_groups[(str(pair["scenarioIdA"]), field)].append(pair)
        elif scope == "cross_scenario":
            cross_groups[
                (
                    str(pair["scenarioIdA"]),
                    str(pair["scenarioIdB"]),
                    field,
                )
            ].append(pair)
        else:
            unknown_groups[field].append(pair)

    for (scenario_id, field), selected in sorted(
        within_groups.items(),
        key=lambda item: (
            item[0][0],
            LEXICAL_FIELD_ORDER[item[0][1]],
        ),
    ):
        rows.append(
            _similarity_summary_row(
                selected,
                "scenario",
                "within_scenario",
                field,
                review_threshold,
                high_threshold,
                scenario_id,
                scenario_id,
            )
        )
    for (scenario_id_a, scenario_id_b, field), selected in sorted(
        cross_groups.items(),
        key=lambda item: (
            item[0][0],
            item[0][1],
            LEXICAL_FIELD_ORDER[item[0][2]],
        ),
    ):
        rows.append(
            _similarity_summary_row(
                selected,
                "scenario_pair",
                "cross_scenario",
                field,
                review_threshold,
                high_threshold,
                scenario_id_a,
                scenario_id_b,
            )
        )
    for field, selected in sorted(unknown_groups.items()):
        rows.append(
            _similarity_summary_row(
                selected,
                "overall",
                "unknown_scenario",
                field,
                review_threshold,
                high_threshold,
            )
        )
    return rows


def analyze_records(
    records: list[dict[str, Any]],
    malformed_lines: int = 0,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    review_threshold: float = DEFAULT_REVIEW_THRESHOLD,
) -> dict[str, Any]:
    """joins records and calculates experiment results"""

    if not 0 <= review_threshold <= similarity_threshold <= 1:
        raise ValueError(
            "thresholds must satisfy 0 <= review_threshold <= "
            "similarity_threshold <= 1"
        )

    # separates story generation records from gameplay events
    generations = [record for record in records if get_record_type(record) == "generation"]
    events = [record for record in records if get_record_type(record) == "gameplay_event"]

    # joins starts and completions by their shared request id
    started_by_request: dict[str, dict[str, Any]] = {}
    completed_by_request: dict[str, dict[str, Any]] = {}
    for event in events:
        request_id = str(event.get("requestId", ""))
        if event.get("eventType") == "scenario_started":
            started_by_request[request_id] = event
        elif event.get("eventType") == "scenario_completed":
            completed_by_request[request_id] = event

    # counts story source validation and openai results
    sources = Counter(str(record.get("source", "unknown")) for record in generations)
    openai_attempts = sum(record.get("openaiAttempted") is True for record in generations)
    openai_successes = sum(record.get("source") == "openai" for record in generations)
    backend_acceptance_values = [
        value for value in (_backend_accepted(record) for record in generations)
        if value is not None
    ]
    unity_acceptance_values = [
        value for value in (_unity_accepted(event) for event in started_by_request.values())
        if value is not None
    ]

    # completion time uses only requests that have both start and completion
    completed_started_requests = set(started_by_request) & set(completed_by_request)
    completion_times = [
        _number(completed_by_request[request_id].get("elapsedSeconds"))
        for request_id in completed_started_requests
    ]

    # adds token and cost data from records that contain usage details
    usage_records = [
        record.get("usage") for record in generations
        if isinstance(record.get("usage"), dict)
    ]
    total_input_tokens = sum(
        int(usage.get("inputTokens", 0) or 0) for usage in usage_records
    )
    total_output_tokens = sum(
        int(usage.get("outputTokens", 0) or 0) for usage in usage_records
    )
    total_tokens = sum(
        int(usage.get("totalTokens", 0) or 0) for usage in usage_records
    )
    total_cost = sum(
        float(usage.get("estimatedCostUsd", 0) or 0) for usage in usage_records
    )

    # Compares the two creative fields separately; title is exact-match only.
    similarity_pairs = build_field_similarity_pairs(
        generations,
        similarity_threshold,
        review_threshold,
    )
    flagged_similarity_pairs = [
        pair
        for pair in similarity_pairs
        if pair["similarityBand"] != "unflagged"
    ]
    similarity_summary_rows = build_field_similarity_summary(
        similarity_pairs,
        review_threshold,
        similarity_threshold,
    )
    title_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for generation in generations:
        narrative = generation.get("narrative")
        if not isinstance(narrative, dict):
            continue
        normalized_title = normalize_text(narrative.get("title", ""))
        if normalized_title:
            title_groups[normalized_title].append(generation)
    repeated_title_groups = {
        title: group for title, group in title_groups.items() if len(group) > 1
    }
    repeated_title_rows = []
    for normalized_title, group in sorted(repeated_title_groups.items()):
        first_narrative = group[0].get("narrative", {})
        repeated_title_rows.append(
            {
                "title": str(first_narrative.get("title", "")),
                "normalizedTitle": normalized_title,
                "occurrences": len(group),
                "scenarioIds": ";".join(
                    sorted(
                        {
                            str(_scenario(record).get("scenarioId", ""))
                            for record in group
                        }
                    )
                ),
                "requestIds": ";".join(
                    str(record.get("requestId", "")) for record in group
                ),
            }
        )

    # collects every scenario id found in generation or gameplay records
    generation_by_request = {
        str(record.get("requestId", "")): record for record in generations
    }
    scenario_ids = {
        str(_scenario(record).get("scenarioId", "unknown"))
        for record in generations
    }
    scenario_ids.update(
        str(event.get("scenarioId", "unknown")) for event in events
    )
    # calculates separate totals for each scenario
    scenario_rows: list[dict[str, Any]] = []
    for scenario_id in sorted(scenario_ids):
        scenario_generations = [
            record for record in generations
            if str(_scenario(record).get("scenarioId", "unknown")) == scenario_id
        ]
        scenario_starts = [
            event for event in started_by_request.values()
            if str(event.get("scenarioId", "unknown")) == scenario_id
        ]
        scenario_start_ids = {
            str(event.get("requestId", "")) for event in scenario_starts
        }
        scenario_completions = [
            event for request_id, event in completed_by_request.items()
            if request_id in scenario_start_ids
        ]
        scenario_rows.append(
            {
                "scenarioId": scenario_id,
                "scenarioType": next(
                    (
                        str(_scenario(record).get("scenarioType", ""))
                        for record in scenario_generations
                    ),
                    next(
                        (
                            str(event.get("scenarioType", ""))
                            for event in scenario_starts
                        ),
                        "",
                    ),
                ),
                "generations": len(scenario_generations),
                "openaiNarratives": sum(
                    record.get("source") == "openai"
                    for record in scenario_generations
                ),
                "fallbackNarratives": sum(
                    record.get("source") == "fallback"
                    for record in scenario_generations
                ),
                "started": len(scenario_starts),
                "completed": len(scenario_completions),
                "completionRate": _rate(
                    len(scenario_completions), len(scenario_starts)
                ),
                "averageCompletionSeconds": _mean(
                    _number(event.get("elapsedSeconds"))
                    for event in scenario_completions
                ),
            }
        )

    # sorts known timestamps to find the report time range
    timestamps = sorted(
        str(record.get("timestampUtc"))
        for record in records
        if record.get("timestampUtc")
    )
    return {
        "records": {
            "valid": len(records),
            "malformed": malformed_lines,
            "unknownType": sum(get_record_type(record) == "unknown" for record in records),
            "schemaVersions": dict(
                sorted(Counter(str(record.get("schemaVersion", "unknown")) for record in records).items())
            ),
            "firstTimestampUtc": timestamps[0] if timestamps else None,
            "lastTimestampUtc": timestamps[-1] if timestamps else None,
        },
        "generation": {
            "total": len(generations),
            "sources": dict(sorted(sources.items())),
            "openaiAttempts": openai_attempts,
            "openaiSuccesses": openai_successes,
            "openaiAttemptSuccessRate": _rate(openai_successes, openai_attempts),
            "fallbacks": sources.get("fallback", 0),
            "fallbackRate": _rate(sources.get("fallback", 0), len(generations)),
            "continuityProvided": sum(_continuity_provided(record) for record in generations),
            "backendValidationKnown": len(backend_acceptance_values),
            "backendAccepted": sum(backend_acceptance_values),
            "backendAcceptanceRate": _rate(
                sum(backend_acceptance_values), len(backend_acceptance_values)
            ),
        },
        "performance": {
            "averageOpenaiLatencySeconds": _mean(
                _number(record.get("performance", {}).get("openaiLatencySeconds"))
                if isinstance(record.get("performance"), dict) else None
                for record in generations
            ),
            "averageBackendLatencySeconds": _mean(
                _number(record.get("performance", {}).get("backendLatencySeconds"))
                if isinstance(record.get("performance"), dict) else None
                for record in generations
            ),
        },
        "usage": {
            "recordsWithUsage": len(usage_records),
            "inputTokens": total_input_tokens,
            "outputTokens": total_output_tokens,
            "totalTokens": total_tokens,
            "averageTokensPerGeneration": _rate(total_tokens, len(usage_records)),
            "estimatedCostUsd": total_cost,
            "averageEstimatedCostUsd": _rate(total_cost, len(usage_records)),
        },
        "gameplay": {
            "started": len(started_by_request),
            "completed": len(completed_started_requests),
            "completionRate": _rate(
                len(completed_started_requests), len(started_by_request)
            ),
            "startedNotCompleted": len(set(started_by_request) - set(completed_by_request)),
            "completedWithoutStart": len(set(completed_by_request) - set(started_by_request)),
            "averageCompletionSeconds": _mean(completion_times),
            "unityValidationKnown": len(unity_acceptance_values),
            "unityAccepted": sum(unity_acceptance_values),
            "unityAcceptanceRate": _rate(
                sum(unity_acceptance_values), len(unity_acceptance_values)
            ),
        },
        "repetition": {
            "metricVersion": LEXICAL_METRIC_VERSION,
            "comparisonMethod": (
                "Symmetric normalized character-sequence similarity by field "
                "(autojunk disabled)"
            ),
            "fields": list(LEXICAL_FIELDS),
            "primaryScope": "within_scenario",
            "secondaryScope": "cross_scenario",
            "reviewThreshold": review_threshold,
            "threshold": similarity_threshold,
            "totalFieldPairs": len(similarity_pairs),
            "withinScenarioFieldPairs": sum(
                pair["comparisonScope"] == "within_scenario"
                for pair in similarity_pairs
            ),
            "crossScenarioFieldPairs": sum(
                pair["comparisonScope"] == "cross_scenario"
                for pair in similarity_pairs
            ),
            "exactFieldPairs": sum(
                pair["similarityBand"] == "exact" for pair in similarity_pairs
            ),
            "reviewFieldPairs": sum(
                pair["similarityBand"] == "review" for pair in similarity_pairs
            ),
            "highNonExactFieldPairs": sum(
                pair["similarityBand"] == "high" for pair in similarity_pairs
            ),
            "repeatedTitleGroups": len(repeated_title_groups),
            "repeatedTitleOccurrences": sum(
                len(group) for group in repeated_title_groups.values()
            ),
            "titleMethod": (
                "Exact match after NFKC, case, punctuation, and whitespace "
                "normalization; excluded from field similarity"
            ),
        },
        "scenarioRows": scenario_rows,
        "similarityPairs": similarity_pairs,
        "flaggedSimilarityPairs": flagged_similarity_pairs,
        "similaritySummaryRows": similarity_summary_rows,
        "repeatedTitleRows": repeated_title_rows,
        "generationRows": build_generation_rows(
            generations,
            started_by_request,
            completed_by_request,
        ),
        "generationByRequest": generation_by_request,
    }


def build_generation_rows(
    generations: list[dict[str, Any]],
    started_by_request: dict[str, dict[str, Any]],
    completed_by_request: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """builds one flat csv row for each story generation"""

    rows: list[dict[str, Any]] = []
    for record in generations:
        request_id = str(record.get("requestId", ""))
        scenario = _scenario(record)
        narrative = record.get("narrative")
        narrative = narrative if isinstance(narrative, dict) else {}
        performance = record.get("performance")
        performance = performance if isinstance(performance, dict) else {}
        usage = record.get("usage")
        usage = usage if isinstance(usage, dict) else {}
        completed_event = completed_by_request.get(request_id, {})
        started_event = started_by_request.get(request_id, {})
        rows.append(
            {
                "requestId": request_id,
                "timestampUtc": record.get("timestampUtc", ""),
                "schemaVersion": record.get("schemaVersion", ""),
                "promptVersion": record.get("promptVersion", ""),
                "scenarioId": scenario.get("scenarioId", ""),
                "scenarioType": scenario.get("scenarioType", ""),
                "requiredAmount": scenario.get("requiredAmount", ""),
                "source": record.get("source", ""),
                "model": record.get("model", ""),
                "fallbackReason": record.get("fallbackReason") or "",
                "continuityProvided": _continuity_provided(record),
                "backendAccepted": _backend_accepted(record),
                "title": narrative.get("title", ""),
                "introduction": narrative.get("introduction", ""),
                "objectiveText": narrative.get("objectiveText", ""),
                "completionText": narrative.get("completionText", ""),
                "storySummary": narrative.get("storySummary", ""),
                "openaiLatencySeconds": performance.get("openaiLatencySeconds", ""),
                "backendLatencySeconds": performance.get("backendLatencySeconds", ""),
                "inputTokens": usage.get("inputTokens", ""),
                "outputTokens": usage.get("outputTokens", ""),
                "totalTokens": usage.get("totalTokens", ""),
                "estimatedCostUsd": usage.get("estimatedCostUsd", ""),
                "started": bool(started_event),
                "completed": bool(completed_event),
                "completionSeconds": completed_event.get("elapsedSeconds", ""),
                "narrativeSourceInUnity": started_event.get("narrativeSource", ""),
                "unityAccepted": _unity_accepted(started_event),
            }
        )
    return rows


def _format_number(value: float | None, digits: int = 3) -> str:
    """formats a number or returns clear missing text"""

    return "N/A" if value is None else f"{value:.{digits}f}"


def _format_rate(value: float | None) -> str:
    """formats a rate as a percentage or missing text"""

    return "N/A" if value is None else f"{value * 100:.1f}%"


def _markdown_cell(value: Any) -> str:
    """escapes free text for one markdown table cell"""

    return str(value or "").replace("\n", " ").replace("|", "\\|")


def render_markdown(analysis: dict[str, Any], input_path: Path) -> str:
    """builds the readable markdown experiment summary"""

    # short names keep the report template easy to read
    records = analysis["records"]
    generation = analysis["generation"]
    performance = analysis["performance"]
    usage = analysis["usage"]
    gameplay = analysis["gameplay"]
    repetition = analysis["repetition"]

    # Starts with overall reliability, performance, and gameplay.
    lines = [
        "# LLM Narrative Experiment Summary",
        "",
        f"Source: `{input_path}`",
        "",
        "## Dataset",
        "",
        f"- Valid records: {records['valid']}",
        f"- Malformed lines skipped: {records['malformed']}",
        f"- Generation records: {generation['total']}",
        f"- Gameplay events: {gameplay['started'] + gameplay['completed'] + gameplay['completedWithoutStart']}",
        f"- Period (UTC): {records['firstTimestampUtc'] or 'N/A'} to {records['lastTimestampUtc'] or 'N/A'}",
        "",
        "## Generation reliability",
        "",
        f"- OpenAI attempts: {generation['openaiAttempts']}",
        f"- OpenAI narratives returned: {generation['openaiSuccesses']}",
        f"- OpenAI attempt success rate: {_format_rate(generation['openaiAttemptSuccessRate'])}",
        f"- Fallback narratives: {generation['fallbacks']}",
        f"- Fallback rate: {_format_rate(generation['fallbackRate'])}",
        f"- Backend acceptance rate (known schema-2 rows): {_format_rate(generation['backendAcceptanceRate'])}",
        f"- Unity acceptance rate (recorded starts): {_format_rate(gameplay['unityAcceptanceRate'])}",
        "",
        "## Performance and cost",
        "",
        f"- Average OpenAI latency: {_format_number(performance['averageOpenaiLatencySeconds'])} s",
        f"- Average backend latency: {_format_number(performance['averageBackendLatencySeconds'])} s",
        f"- Total input tokens: {usage['inputTokens']}",
        f"- Total output tokens: {usage['outputTokens']}",
        f"- Total tokens: {usage['totalTokens']}",
        f"- Average tokens per measured generation: {_format_number(usage['averageTokensPerGeneration'], 1)}",
        f"- Estimated total cost: ${usage['estimatedCostUsd']:.6f}",
        f"- Average estimated cost: ${_format_number(usage['averageEstimatedCostUsd'], 6)}",
        "",
        "## Gameplay",
        "",
        f"- Scenarios started: {gameplay['started']}",
        f"- Scenarios completed: {gameplay['completed']}",
        f"- Completion rate: {_format_rate(gameplay['completionRate'])}",
        f"- Started but not completed: {gameplay['startedNotCompleted']}",
        f"- Average completion time: {_format_number(gameplay['averageCompletionSeconds'])} s",
        "",
        "## Gameplay by scenario",
        "",
        "| Scenario | Type | Generated | OpenAI | Fallback | Started | Completed | Completion rate | Avg. completion (s) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    # adds one table row for each scenario
    for row in analysis["scenarioRows"]:
        lines.append(
            "| {scenarioId} | {scenarioType} | {generations} | "
            "{openaiNarratives} | {fallbackNarratives} | {started} | "
            "{completed} | {completion_rate} | {completion_time} |".format(
                **row,
                completion_rate=_format_rate(row["completionRate"]),
                completion_time=_format_number(row["averageCompletionSeconds"]),
            )
        )

    lines.extend(
        [
            "",
            "## Narrative lexical diversity (field-level v2)",
            "",
            f"- Metric version: `{repetition['metricVersion']}`",
            f"- Method: {repetition['comparisonMethod']}",
            "- Primary analysis: compare `introduction` and `completionText` "
            "separately within the same scenario.",
            "- Secondary analysis: compare the same fields across scenarios.",
            f"- Review band: {repetition['reviewThreshold']:.0%} to below "
            f"{repetition['threshold']:.0%}; high similarity: "
            f"{repetition['threshold']:.0%} or above.",
            "- Title: exact normalized repetition only; it does not affect the "
            "introduction/completion similarity scores.",
            "",
            "> Text is normalized with Unicode NFKC, case folding, punctuation "
            "removal, and whitespace collapse. This is a lexical wording "
            "baseline—not semantic similarity or a human quality score. "
            "`objectiveText`, display names, and `storySummary` are excluded.",
            "",
            "### Overall field comparison",
            "",
            "| Analysis role | Scope | Field | Narratives | Pairs | Mean | Median | P90 | Max | Exact | Review | High or exact |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    overall_rows = [
        row
        for row in analysis["similaritySummaryRows"]
        if row["aggregation"] == "overall"
        and row["comparisonScope"] in {"within_scenario", "cross_scenario"}
    ]
    for row in overall_rows:
        role = "Primary" if row["comparisonScope"] == "within_scenario" else "Secondary"
        lines.append(
            f"| {role} | {row['comparisonScope']} | `{row['field']}` | "
            f"{row['narrativesCompared']} | {row['comparisons']} | "
            f"{_format_number(row['meanSimilarity'])} | "
            f"{_format_number(row['medianSimilarity'])} | "
            f"{_format_number(row['p90Similarity'])} | "
            f"{_format_number(row['maximumSimilarity'])} | "
            f"{row['exactPairs']} ({_format_rate(row['exactPairRate'])}) | "
            f"{row['reviewPairs']} ({_format_rate(row['reviewPairRate'])}) | "
            f"{row['highOrExactPairs']} "
            f"({_format_rate(row['highOrExactPairRate'])}) |"
        )

    # Scenario-level within-scenario results are the main inferential view.
    lines.extend(
        [
            "",
            "### Primary within-scenario results",
            "",
            "| Scenario | Field | Narratives | Pairs | Mean | P90 | Max | Exact | Review | High or exact |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    within_rows = [
        row
        for row in analysis["similaritySummaryRows"]
        if row["aggregation"] == "scenario"
        and row["comparisonScope"] == "within_scenario"
    ]
    if not within_rows:
        lines.append("| N/A | N/A | 0 | 0 | N/A | N/A | N/A | 0 | 0 | 0 |")
    else:
        for row in within_rows:
            lines.append(
                f"| {_markdown_cell(row['scenarioIdA'])} | `{row['field']}` | "
                f"{row['narrativesCompared']} | {row['comparisons']} | "
                f"{_format_number(row['meanSimilarity'])} | "
                f"{_format_number(row['p90Similarity'])} | "
                f"{_format_number(row['maximumSimilarity'])} | "
                f"{row['exactPairs']} ({_format_rate(row['exactPairRate'])}) | "
                f"{row['reviewPairs']} ({_format_rate(row['reviewPairRate'])}) | "
                f"{row['highOrExactPairs']} "
                f"({_format_rate(row['highOrExactPairRate'])}) |"
            )

    # Keep the readable report short; the CSV preserves all pair scores and text.
    lines.extend(["", "### Flagged field pairs", ""])
    if not analysis["flaggedSimilarityPairs"]:
        lines.append("No review, high-similarity, or exact field pairs were found.")
    else:
        lines.extend(
            [
                "| Scope | Field | Band | Similarity | Scenario A | Scenario B | Title A | Title B | Request A | Request B |",
                "|---|---|---|---:|---|---|---|---|---|---|",
            ]
        )
        for pair in analysis["flaggedSimilarityPairs"][:25]:
            lines.append(
                f"| {pair['comparisonScope']} | `{pair['field']}` | "
                f"{pair['similarityBand']} | {pair['similarity']:.1%} | "
                f"{_markdown_cell(pair['scenarioIdA'])} | "
                f"{_markdown_cell(pair['scenarioIdB'])} | "
                f"{_markdown_cell(pair['titleA'])} | "
                f"{_markdown_cell(pair['titleB'])} | "
                f"`{_markdown_cell(pair['requestIdA'])}` | "
                f"`{_markdown_cell(pair['requestIdB'])}` |"
            )
        if len(analysis["flaggedSimilarityPairs"]) > 25:
            lines.append(
                ""
            )
            lines.append(
                f"Only the first 25 flagged pairs are shown here; all "
                f"{len(analysis['similarityPairs'])} comparisons are in "
                "`similar_narratives.csv`."
            )

    lines.extend(["", "### Repeated titles (secondary exact-only check)", ""])
    lines.append(f"Method: {repetition['titleMethod']}.")
    lines.append("")
    if not analysis["repeatedTitleRows"]:
        lines.append("No repeated normalized titles were found.")
    else:
        lines.extend(
            [
                "| Title | Occurrences | Scenario IDs |",
                "|---|---:|---|",
            ]
        )
        for row in analysis["repeatedTitleRows"]:
            lines.append(
                f"| {_markdown_cell(row['title'])} | {row['occurrences']} | "
                f"{_markdown_cell(row['scenarioIds'])} |"
            )
    return "\n".join(lines) + "\n"


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str] | None = None,
) -> None:
    """writes dictionary rows into one csv file"""

    # creates the folder before opening the output file
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(rows[0].keys()) if rows else (fieldnames or [])
    # writes an empty file when there are no known columns
    if not columns:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(
    analysis: dict[str, Any],
    input_path: Path,
    output_directory: Path,
) -> list[Path]:
    """writes the markdown summary and all csv reports"""

    # prepares each output path in one report folder
    output_directory.mkdir(parents=True, exist_ok=True)
    summary_path = output_directory / "experiment_summary.md"
    generations_path = output_directory / "generation_records.csv"
    scenarios_path = output_directory / "scenario_summary.csv"
    similarity_path = output_directory / "similar_narratives.csv"
    repeated_titles_path = output_directory / "repeated_titles.csv"
    lexical_summary_path = output_directory / "lexical_field_summary.csv"

    # writes the main report and flat generation and scenario tables
    summary_path.write_text(
        render_markdown(analysis, input_path),
        encoding="utf-8",
    )
    write_csv(generations_path, analysis["generationRows"])
    write_csv(scenarios_path, analysis["scenarioRows"])
    # keeps useful column names even when pair reports have no rows
    write_csv(
        similarity_path,
        analysis["similarityPairs"],
        fieldnames=[
            "metricVersion",
            "reviewThreshold",
            "highThreshold",
            "field",
            "comparisonScope",
            "scenarioIdA",
            "scenarioIdB",
            "requestIdA",
            "requestIdB",
            "sourceA",
            "sourceB",
            "modelA",
            "modelB",
            "promptVersionA",
            "promptVersionB",
            "titleA",
            "titleB",
            "textA",
            "textB",
            "similarity",
            "similarityBand",
            "exactNormalizedText",
        ],
    )
    write_csv(
        repeated_titles_path,
        analysis["repeatedTitleRows"],
        fieldnames=[
            "title",
            "normalizedTitle",
            "occurrences",
            "scenarioIds",
            "requestIds",
        ],
    )
    write_csv(
        lexical_summary_path,
        analysis["similaritySummaryRows"],
        fieldnames=[
            "metricVersion",
            "reviewThreshold",
            "highThreshold",
            "aggregation",
            "comparisonScope",
            "scenarioIdA",
            "scenarioIdB",
            "field",
            "narrativesCompared",
            "comparisons",
            "meanSimilarity",
            "medianSimilarity",
            "p90Similarity",
            "maximumSimilarity",
            "exactPairs",
            "exactPairRate",
            "reviewPairs",
            "reviewPairRate",
            "highNonExactPairs",
            "highNonExactPairRate",
            "highOrExactPairs",
            "highOrExactPairRate",
        ],
    )
    return [
        summary_path,
        generations_path,
        scenarios_path,
        similarity_path,
        repeated_titles_path,
        lexical_summary_path,
    ]


def parse_arguments() -> argparse.Namespace:
    """reads input output and similarity command line settings"""

    parser = argparse.ArgumentParser(
        description=(
            "Analyze narrative JSONL locally and produce Markdown/CSV reports."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help=f"JSONL input (default: {DEFAULT_INPUT_PATH})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIRECTORY,
        help=f"Report directory (default: {DEFAULT_OUTPUT_DIRECTORY})",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=DEFAULT_SIMILARITY_THRESHOLD,
        help="High lexical similarity threshold from 0 to 1 (default: 0.85)",
    )
    parser.add_argument(
        "--review-threshold",
        type=float,
        default=DEFAULT_REVIEW_THRESHOLD,
        help="Lexical review threshold from 0 to 1 (default: 0.80)",
    )
    # The review band begins below the high-similarity threshold.
    arguments = parser.parse_args()
    if not 0 <= arguments.review_threshold <= arguments.similarity_threshold <= 1:
        parser.error(
            "thresholds must satisfy 0 <= --review-threshold <= "
            "--similarity-threshold <= 1"
        )
    return arguments


def main() -> int:
    """runs local analysis and writes all report files"""

    # resolves user paths before reading or writing files
    arguments = parse_arguments()
    input_path = arguments.input.expanduser().resolve()
    output_directory = arguments.output_dir.expanduser().resolve()
    # stops with a failure code when the input log is missing
    if not input_path.is_file():
        print(f"Input log does not exist: {input_path}")
        return 1

    # loads valid records analyzes them and writes every output
    records, errors = load_jsonl(input_path)
    analysis = analyze_records(
        records,
        malformed_lines=len(errors),
        similarity_threshold=arguments.similarity_threshold,
        review_threshold=arguments.review_threshold,
    )
    output_paths = write_outputs(analysis, input_path, output_directory)

    # prints a short result summary and every output path
    print("Experiment analysis complete (offline; no LLM API call).")
    print(f"Valid records: {analysis['records']['valid']}")
    print(f"Generations: {analysis['generation']['total']}")
    print(f"Scenarios completed: {analysis['gameplay']['completed']}")
    print(f"Estimated total cost: ${analysis['usage']['estimatedCostUsd']:.6f}")
    for output_path in output_paths:
        print(f"Wrote: {output_path}")
    # reports up to five bad input lines without stopping valid analysis
    if errors:
        print(f"Warning: skipped {len(errors)} malformed line(s).")
        for error in errors[:5]:
            print(f"  {error}")
    return 0


if __name__ == "__main__":
    # returns the main result as the command exit code
    raise SystemExit(main())

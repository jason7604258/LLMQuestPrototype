#!/usr/bin/env python3
"""Reproducible sentence-embedding analysis for frozen quest narratives.

The script keeps the lexical pair manifest and audit sample unchanged, embeds
the two narrative fields separately, and computes cosine similarity offline.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

from analyze_experiments import get_record_type
from analyze_lexical_similarity import (
    DEFAULT_INPUT_PATH,
    DEFAULT_MAX_LINES,
    FROZEN_GENERATION_COUNT,
    FROZEN_PREFIX_SHA256,
    FROZEN_SCENARIO_GENERATION_COUNTS,
    LEXICAL_FIELDS,
    _percentile,
    build_within_scenario_field_rows,
    load_jsonl_prefix,
    verify_prefix_hash,
    write_csv,
)


BACKEND_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIRECTORY = (
    BACKEND_DIRECTORY / "reports" / "semantic_frozen72_v1"
)
DEFAULT_LEXICAL_DIRECTORY = (
    BACKEND_DIRECTORY / "reports" / "lexical_frozen72_v3"
)
DEFAULT_LEXICAL_PAIRS_PATH = (
    DEFAULT_LEXICAL_DIRECTORY / "within_scenario_lexical_pairs.csv"
)
DEFAULT_LEXICAL_AUDIT_PATH = (
    DEFAULT_LEXICAL_DIRECTORY / "hash_ranked_audit_sample_40.csv"
)
DEFAULT_MODEL_ID = "sentence-transformers/all-mpnet-base-v2"
DEFAULT_MODEL_REVISION = "e8c3b32edf5434bc2275fc9bab85f82640a19130"
DEFAULT_BATCH_SIZE = 32
DEFAULT_TOP_K = 10
SEMANTIC_METRIC_VERSION = "semantic-field-v1-mpnet-cosine"
FROZEN_LEXICAL_PAIRS_SHA256 = (
    "79d5cfc9a95490de12e66087499d1f9e055e31c84a8863c0e702358906d29d7a"
)
FROZEN_LEXICAL_AUDIT_SHA256 = (
    "1dc5472400c157bcb6bb6f0374c6496c8d928809d14780ebf9878d5b3a2efc3d"
)
FROZEN_AUDIT_PAIR_COUNT = 40
PAIR_KEY_FIELDS = (
    "comparisonScope",
    "scenarioId",
    "field",
    "requestIdA",
    "requestIdB",
)


def semantic_text(value: Any) -> str:
    """Collapse whitespace while preserving case, words, and punctuation."""

    return " ".join(str(value or "").split())


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_fingerprint(path: Path) -> tuple[str, list[dict[str, Any]]]:
    """Hash resolved model files and their relative names into one manifest."""

    entries: list[dict[str, Any]] = []
    combined = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if not item.is_file():
            continue
        relative = str(item.relative_to(path))
        file_hash = _sha256_file(item)
        size = item.stat().st_size
        entries.append(
            {"relativePath": relative, "bytes": size, "sha256": file_hash}
        )
        combined.update(relative.encode("utf-8"))
        combined.update(b"\0")
        combined.update(file_hash.encode("ascii"))
        combined.update(b"\n")
    return combined.hexdigest(), entries


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def field_join_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return tuple(str(row.get(field, "")) for field in PAIR_KEY_FIELDS)  # type: ignore[return-value]


def pair_join_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("scenarioId", "")),
        str(row.get("requestIdA", "")),
        str(row.get("requestIdB", "")),
    )


def identity_key(
    scenario_id: str, field: str, request_id: str
) -> tuple[str, str, str]:
    return (scenario_id, field, request_id)


def validate_lexical_manifest(
    generated_rows: list[dict[str, Any]],
    persisted_rows: list[dict[str, str]],
) -> None:
    """Require exact lexical pair keys, order, source texts, and metrics."""

    generated_keys = [field_join_key(row) for row in generated_rows]
    persisted_keys = [field_join_key(row) for row in persisted_rows]
    if len(set(generated_keys)) != len(generated_keys):
        raise ValueError("generated lexical manifest contains duplicate field keys")
    if len(set(persisted_keys)) != len(persisted_keys):
        raise ValueError("persisted lexical manifest contains duplicate field keys")
    if generated_keys != persisted_keys:
        raise ValueError(
            "persisted lexical field keys/order do not match the frozen input"
        )
    for generated, persisted in zip(generated_rows, persisted_rows):
        for field in ("titleA", "titleB", "textA", "textB"):
            if str(generated.get(field, "")) != str(persisted.get(field, "")):
                raise ValueError(
                    f"persisted lexical {field} differs for {field_join_key(generated)}"
                )
        if str(generated.get("metricVersion", "")) != str(
            persisted.get("metricVersion", "")
        ):
            raise ValueError(
                "persisted lexical metricVersion differs for "
                f"{field_join_key(generated)}"
            )
        for metric in (
            "word1gramJaccard",
            "tokenLcsF1",
            "word3gramJaccard",
        ):
            generated_value = generated.get(metric)
            persisted_text = str(persisted.get(metric, "")).strip()
            if generated_value is None:
                if persisted_text:
                    raise ValueError(
                        f"persisted lexical {metric} should be blank for "
                        f"{field_join_key(generated)}"
                    )
                continue
            try:
                persisted_value = float(persisted_text)
            except ValueError as error:
                raise ValueError(
                    f"persisted lexical {metric} is not numeric for "
                    f"{field_join_key(generated)}"
                ) from error
            # The lexical CSV deliberately serializes floats to six decimals.
            if not math.isclose(
                float(generated_value),
                persisted_value,
                rel_tol=0.0,
                abs_tol=0.0000005,
            ):
                raise ValueError(
                    f"persisted lexical {metric} differs for "
                    f"{field_join_key(generated)}"
                )
        generated_exact = bool(generated.get("exactNormalizedText"))
        persisted_exact_text = str(
            persisted.get("exactNormalizedText", "")
        ).strip().casefold()
        if persisted_exact_text not in {"true", "false"}:
            raise ValueError(
                "persisted lexical exactNormalizedText is not Boolean for "
                f"{field_join_key(generated)}"
            )
        if generated_exact != (persisted_exact_text == "true"):
            raise ValueError(
                "persisted lexical exactNormalizedText differs for "
                f"{field_join_key(generated)}"
            )


def collect_text_identities(
    lexical_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Return one original semantic text for each scenario/field/request."""

    identities: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in lexical_rows:
        scenario_id = str(row["scenarioId"])
        field = str(row["field"])
        for side in ("A", "B"):
            request_id = str(row[f"requestId{side}"])
            text = semantic_text(row[f"text{side}"])
            if not text:
                raise ValueError(
                    f"empty semantic text for {(scenario_id, field, request_id)}"
                )
            key = identity_key(scenario_id, field, request_id)
            candidate = {
                "scenarioId": scenario_id,
                "field": field,
                "requestId": request_id,
                "title": str(row[f"title{side}"]),
                "text": text,
                "textSha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
            previous = identities.get(key)
            if previous is not None and previous != candidate:
                raise ValueError(f"conflicting semantic text identity: {key}")
            identities[key] = candidate
    field_order = {field: index for index, field in enumerate(LEXICAL_FIELDS)}
    return sorted(
        identities.values(),
        key=lambda row: (
            row["scenarioId"],
            field_order[row["field"]],
            row["requestId"],
        ),
    )


def cosine_from_normalized(
    left: Sequence[float], right: Sequence[float]
) -> float:
    """Return dot product, equivalent to cosine for L2-normalized vectors."""

    if len(left) != len(right):
        raise ValueError("embedding dimensions differ")
    value = math.fsum(float(a) * float(b) for a, b in zip(left, right))
    if not math.isfinite(value):
        raise ValueError("embedding cosine is not finite")
    return min(1.0, max(-1.0, value))


def encode_identities(
    model: Any,
    identity_rows: list[dict[str, Any]],
    batch_size: int,
) -> tuple[
    dict[tuple[str, str, str], Sequence[float]],
    dict[tuple[str, str, str], dict[str, Any]],
]:
    """Tokenize for truncation diagnostics and encode every identity once."""

    texts = [str(row["text"]) for row in identity_rows]
    tokenized = model.tokenizer(
        texts,
        add_special_tokens=True,
        padding=False,
        truncation=False,
    )
    token_ids = tokenized["input_ids"]
    max_sequence_length = int(model.max_seq_length)
    diagnostics: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row, ids in zip(identity_rows, token_ids):
        key = identity_key(row["scenarioId"], row["field"], row["requestId"])
        diagnostics[key] = {
            "wordpieces": len(ids),
            "wouldTruncate": len(ids) > max_sequence_length,
        }

    matrix = model.encode(
        texts,
        batch_size=batch_size,
        precision="float32",
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    embeddings: dict[tuple[str, str, str], Sequence[float]] = {}
    for row, vector in zip(identity_rows, matrix):
        key = identity_key(row["scenarioId"], row["field"], row["requestId"])
        if not all(math.isfinite(float(value)) for value in vector):
            raise ValueError(f"embedding contains a non-finite value: {key}")
        embeddings[key] = vector
        norm = math.sqrt(
            math.fsum(float(value) ** 2 for value in vector)
        )
        if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=0.00001):
            raise ValueError(f"embedding is not L2-normalized: {key} ({norm})")
        diagnostics[key]["embeddingNorm"] = norm
    if len(embeddings) != len(identity_rows):
        raise ValueError("encoder did not return exactly one vector per identity")
    return embeddings, diagnostics


def _float(row: dict[str, Any], field: str) -> float:
    value = row.get(field)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return float(str(value))


def build_semantic_rows(
    lexical_rows: list[dict[str, str]],
    embeddings: dict[tuple[str, str, str], Sequence[float]],
    diagnostics: dict[tuple[str, str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Add semantic cosine and diagnostics without changing lexical row order."""

    results: list[dict[str, Any]] = []
    for row in lexical_rows:
        scenario_id = str(row["scenarioId"])
        field = str(row["field"])
        key_a = identity_key(scenario_id, field, str(row["requestIdA"]))
        key_b = identity_key(scenario_id, field, str(row["requestIdB"]))
        if key_a not in embeddings or key_b not in embeddings:
            raise ValueError(f"missing embedding for {key_a} or {key_b}")
        cosine = cosine_from_normalized(embeddings[key_a], embeddings[key_b])
        results.append(
            {
                "semanticMetricVersion": SEMANTIC_METRIC_VERSION,
                "comparisonScope": row["comparisonScope"],
                "scenarioId": scenario_id,
                "field": field,
                "requestIdA": row["requestIdA"],
                "requestIdB": row["requestIdB"],
                "titleA": row["titleA"],
                "titleB": row["titleB"],
                "textA": row["textA"],
                "textB": row["textB"],
                "wordpiecesA": diagnostics[key_a]["wordpieces"],
                "wordpiecesB": diagnostics[key_b]["wordpieces"],
                "wouldTruncateA": diagnostics[key_a]["wouldTruncate"],
                "wouldTruncateB": diagnostics[key_b]["wouldTruncate"],
                "semanticCosine": cosine,
                "word1gramJaccard": _float(row, "word1gramJaccard"),
                "tokenLcsF1": _float(row, "tokenLcsF1"),
                "word3gramJaccard": _float(row, "word3gramJaccard"),
                "exactNormalizedText": row["exactNormalizedText"],
            }
        )
    return results


def build_embedding_manifest(
    identity_rows: list[dict[str, Any]],
    diagnostics: dict[tuple[str, str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for row in identity_rows:
        key = identity_key(row["scenarioId"], row["field"], row["requestId"])
        results.append(
            {
                **row,
                "wordpieces": diagnostics[key]["wordpieces"],
                "wouldTruncate": diagnostics[key]["wouldTruncate"],
                "embeddingNorm": diagnostics[key]["embeddingNorm"],
            }
        )
    return results


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _summary_row(
    rows: list[dict[str, Any]],
    aggregation: str,
    field: str,
    scenario_id: str = "",
) -> dict[str, Any]:
    values = [_float(row, "semanticCosine") for row in rows]
    request_ids = {
        (str(row["scenarioId"]), str(row[key]))
        for row in rows
        for key in ("requestIdA", "requestIdB")
    }
    truncated_pairs = sum(
        bool(row["wouldTruncateA"]) or bool(row["wouldTruncateB"])
        for row in rows
    )
    return {
        "semanticMetricVersion": SEMANTIC_METRIC_VERSION,
        "aggregation": aggregation,
        "comparisonScope": "within_scenario",
        "scenarioId": scenario_id,
        "field": field,
        "narrativesCompared": len(request_ids),
        "comparisons": len(rows),
        "meanSemanticCosine": statistics.fmean(values) if values else None,
        "medianSemanticCosine": statistics.median(values) if values else None,
        "p90SemanticCosine": _percentile(values, 0.90),
        "minimumSemanticCosine": min(values) if values else None,
        "maximumSemanticCosine": max(values) if values else None,
        "pairsWithTruncation": truncated_pairs,
        "pairTruncationRate": _rate(truncated_pairs, len(rows)),
        "macroMeanOfScenarioMeans": None,
    }


def build_summary_rows(
    semantic_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build pooled pair-weighted and exact-scenario semantic summaries."""

    scenario_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in semantic_rows:
        scenario_groups[(str(row["scenarioId"]), str(row["field"]))].append(row)

    results: list[dict[str, Any]] = []
    for field in LEXICAL_FIELDS:
        selected = [row for row in semantic_rows if row["field"] == field]
        overall = _summary_row(selected, "overall_pair_weighted", field)
        scenario_means = [
            statistics.fmean(
                _float(row, "semanticCosine") for row in group
            )
            for (scenario_id, grouped_field), group in scenario_groups.items()
            if grouped_field == field
        ]
        overall["macroMeanOfScenarioMeans"] = (
            statistics.fmean(scenario_means) if scenario_means else None
        )
        results.append(overall)

    field_order = {field: index for index, field in enumerate(LEXICAL_FIELDS)}
    for (scenario_id, field), selected in sorted(
        scenario_groups.items(),
        key=lambda item: (item[0][0], field_order[item[0][1]]),
    ):
        results.append(_summary_row(selected, "scenario", field, scenario_id))
    return results


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right):
        raise ValueError("correlation vectors differ in length")
    if len(left) < 2:
        return None
    mean_left = statistics.fmean(left)
    mean_right = statistics.fmean(right)
    numerator = math.fsum(
        (a - mean_left) * (b - mean_right) for a, b in zip(left, right)
    )
    denominator = math.sqrt(
        math.fsum((value - mean_left) ** 2 for value in left)
        * math.fsum((value - mean_right) ** 2 for value in right)
    )
    return numerator / denominator if denominator else None


def _average_ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    ranks = [0.0] * len(values)
    start = 0
    while start < len(indexed):
        end = start + 1
        while end < len(indexed) and indexed[end][1] == indexed[start][1]:
            end += 1
        average_rank = ((start + 1) + end) / 2
        for position in range(start, end):
            ranks[indexed[position][0]] = average_rank
        start = end
    return ranks


def _spearman(left: list[float], right: list[float]) -> float | None:
    return _pearson(_average_ranks(left), _average_ranks(right))


def build_correlation_rows(
    semantic_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Describe lexical/semantic association without independence p-values."""

    results: list[dict[str, Any]] = []
    metric_roles = (
        ("tokenLcsF1", "primary_ordered_lexical_overlap"),
        ("word3gramJaccard", "strict_phrase_overlap"),
        ("word1gramJaccard", "descriptive_vocabulary_overlap"),
    )
    for field in LEXICAL_FIELDS:
        selected = [row for row in semantic_rows if row["field"] == field]
        semantic_values = [_float(row, "semanticCosine") for row in selected]
        for metric, role in metric_roles:
            lexical_values = [_float(row, metric) for row in selected]
            results.append(
                {
                    "semanticMetricVersion": SEMANTIC_METRIC_VERSION,
                    "aggregation": "overall_pair_weighted",
                    "comparisonScope": "within_scenario",
                    "field": field,
                    "lexicalMetric": metric,
                    "lexicalMetricRole": role,
                    "comparisons": len(selected),
                    "spearmanRho": _spearman(
                        semantic_values, lexical_values
                    ),
                    "pearsonR": _pearson(semantic_values, lexical_values),
                    "pValueReported": False,
                }
            )
    return results


def build_top_rows(
    semantic_rows: list[dict[str, Any]], top_k: int
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for field in LEXICAL_FIELDS:
        selected = [row for row in semantic_rows if row["field"] == field]
        selected.sort(
            key=lambda row: (
                -_float(row, "semanticCosine"),
                row["scenarioId"],
                row["requestIdA"],
                row["requestIdB"],
            )
        )
        for rank, row in enumerate(selected[:top_k], start=1):
            results.append(
                {
                    "semanticMetricVersion": SEMANTIC_METRIC_VERSION,
                    "field": field,
                    "rankingMetric": "semanticCosine",
                    "metricRole": "primary_overall_semantic_similarity",
                    "rank": rank,
                    "rankingScore": row["semanticCosine"],
                    "scenarioId": row["scenarioId"],
                    "requestIdA": row["requestIdA"],
                    "requestIdB": row["requestIdB"],
                    "titleA": row["titleA"],
                    "titleB": row["titleB"],
                    "semanticCosine": row["semanticCosine"],
                    "tokenLcsF1": row["tokenLcsF1"],
                    "word3gramJaccard": row["word3gramJaccard"],
                    "word1gramJaccard": row["word1gramJaccard"],
                    "textA": row["textA"],
                    "textB": row["textB"],
                }
            )
    return results


def enrich_audit_rows(
    audit_rows: list[dict[str, str]],
    semantic_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Preserve the existing 40 rows/order and append both field cosines."""

    semantic_by_key = {field_join_key(row): row for row in semantic_rows}
    if len(semantic_by_key) != len(semantic_rows):
        raise ValueError("semantic rows contain duplicate field keys")
    seen_pairs: set[tuple[str, str, str]] = set()
    results: list[dict[str, Any]] = []
    for audit in audit_rows:
        pair_key = pair_join_key(audit)
        if pair_key in seen_pairs:
            raise ValueError(f"audit contains duplicate pair key: {pair_key}")
        seen_pairs.add(pair_key)
        values: dict[str, float] = {}
        for field in LEXICAL_FIELDS:
            key = (
                "within_scenario",
                pair_key[0],
                field,
                pair_key[1],
                pair_key[2],
            )
            semantic = semantic_by_key.get(key)
            if semantic is None:
                raise ValueError(f"audit pair is missing semantic field row: {key}")
            values[field] = _float(semantic, "semanticCosine")
        results.append(
            {
                **audit,
                "semanticMetricVersion": SEMANTIC_METRIC_VERSION,
                "introductionSemanticCosine": values["introduction"],
                "completionSemanticCosine": values["completionText"],
            }
        )
    return results


def _format_number(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.4f}"


def _markdown(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_summary(
    metadata: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    correlation_rows: list[dict[str, Any]],
    top_rows: list[dict[str, Any]],
) -> str:
    lines = [
        f"# Semantic Similarity Analysis ({metadata['generationRecords']} generations)",
        "",
        "## Dataset and model",
        "",
        f"- Frozen physical-line prefix: {metadata['linesRead']}",
        f"- Input prefix SHA-256 verified: {str(metadata['inputPrefixHashVerified']).lower()}",
        f"- Generation records: {metadata['generationRecords']}",
        f"- Within-scenario narrative pairs: {metadata['withinScenarioPairs']}",
        f"- Field comparisons: {metadata['fieldComparisons']}",
        f"- Unique embedded field texts: {metadata['uniqueEmbeddedTexts']}",
        f"- Model: `{metadata['modelId']}`",
        f"- Model revision: `{metadata['modelRevision']}`",
        f"- Embedding dimension: {metadata['embeddingDimension']}",
        f"- Device/dtype: `{metadata['device']}` / `{metadata['dtype']}`",
        f"- Maximum model sequence: {metadata['modelMaxSequenceLength']} wordpieces",
        f"- Maximum observed sequence: {metadata['maximumObservedWordpieces']} wordpieces",
        f"- Texts that would be truncated: {metadata['truncatedTextCount']}",
        "",
        "## Method",
        "",
        "Original `introduction` and `completionText` are kept separate. Semantic "
        "preprocessing only collapses whitespace; case, punctuation, stopwords, and "
        "word forms are preserved. Each text is encoded once as an L2-normalized "
        "float32 sentence vector. Cosine similarity is the dot product of the two "
        "normalized vectors and ranges from -1 to 1; it is not a probability or a "
        "percentage.",
        "",
        "No semantic high/review cutoff is assigned. The tables are descriptive, "
        "and overall statistics are pooled pair-weighted. The macro mean gives each "
        f"of the {metadata['scenarioCount']} scenarios equal weight as a sensitivity "
        "result.",
        "",
        "## Overall within-scenario results",
        "",
        "| Field | Pairs | Pair-weighted mean | Macro mean of scenarios | Median | P90 | Minimum | Maximum |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        if row["aggregation"] != "overall_pair_weighted":
            continue
        lines.append(
            f"| `{row['field']}` | {row['comparisons']} | "
            f"{_format_number(row['meanSemanticCosine'])} | "
            f"{_format_number(row['macroMeanOfScenarioMeans'])} | "
            f"{_format_number(row['medianSemanticCosine'])} | "
            f"{_format_number(row['p90SemanticCosine'])} | "
            f"{_format_number(row['minimumSemanticCosine'])} | "
            f"{_format_number(row['maximumSemanticCosine'])} |"
        )

    lines.extend(
        [
            "",
            "## Per-scenario results",
            "",
            "| Scenario | Field | Pairs | Mean | Median | P90 | Maximum |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in summary_rows:
        if row["aggregation"] != "scenario":
            continue
        lines.append(
            f"| `{row['scenarioId']}` | `{row['field']}` | "
            f"{row['comparisons']} | "
            f"{_format_number(row['meanSemanticCosine'])} | "
            f"{_format_number(row['medianSemanticCosine'])} | "
            f"{_format_number(row['p90SemanticCosine'])} | "
            f"{_format_number(row['maximumSemanticCosine'])} |"
        )

    lines.extend(
        [
            "",
            "## Relationship with lexical metrics",
            "",
            "Spearman is primary because the bounded scores need not be linearly "
            "related and Word 3-gram has many ties at zero. Pearson is supplementary. "
            "No p-values are reported because pair observations reuse narratives and "
            "are not independent. These are pooled descriptive correlations, so they "
            "may also include differences among scenarios.",
            "",
            "| Field | Lexical metric | Pairs | Spearman rho | Pearson r |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in correlation_rows:
        lines.append(
            f"| `{row['field']}` | `{row['lexicalMetric']}` | "
            f"{row['comparisons']} | {_format_number(row['spearmanRho'])} | "
            f"{_format_number(row['pearsonR'])} |"
        )

    lines.extend(
        [
            "",
            "## Highest semantic-cosine pairs",
            "",
            "| Field | Rank | Cosine | LCS F1 | Scenario | Title A | Title B | Request A | Request B |",
            "|---|---:|---:|---:|---|---|---|---|---|",
        ]
    )
    for row in top_rows:
        if int(row["rank"]) > 5:
            continue
        lines.append(
            f"| `{row['field']}` | {row['rank']} | "
            f"{_format_number(row['semanticCosine'])} | "
            f"{_format_number(row['tokenLcsF1'])} | "
            f"`{row['scenarioId']}` | {_markdown(row['titleA'])} | "
            f"{_markdown(row['titleB'])} | `{row['requestIdA']}` | "
            f"`{row['requestIdB']}` |"
        )

    lines.extend(
        [
            "",
            "## Audit and interpretation limits",
            "",
            f"The existing {metadata['auditPairs']} hash-ranked audit pairs are "
            "preserved in their original order and enriched with both field-level "
            "semantic scores. They were not resampled using semantic results.",
            "",
            "Same-scenario texts necessarily share enemies, places, objectives, and "
            "events. A high cosine can therefore reflect correct scenario adherence, "
            "not merely poor creativity. Completion texts are shorter and more "
            "functionally constrained than introductions. Sentence embeddings also "
            "compress a whole passage into one vector and cannot locate copied wording; "
            "interpret them beside Token LCS F1, Word 3-gram Jaccard, and the original "
            "texts. No two scores are averaged into a single quality score.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(
    output_directory: Path,
    metadata: dict[str, Any],
    semantic_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    correlation_rows: list[dict[str, Any]],
    top_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    embedding_manifest: list[dict[str, Any]],
) -> list[Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": output_directory / "semantic_analysis_summary.md",
        "metadata": output_directory / "analysis_metadata.json",
        "pairs": output_directory / "within_scenario_semantic_pairs.csv",
        "fieldSummary": output_directory / "within_scenario_semantic_summary.csv",
        "correlations": output_directory / "lexical_semantic_correlations.csv",
        "top": output_directory / "top_semantic_pairs.csv",
        "audit": output_directory
        / f"hash_ranked_audit_sample_{len(audit_rows)}_with_semantic.csv",
        "embeddings": output_directory / "embedded_text_manifest.csv",
    }
    paths["metadata"].write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_csv(paths["pairs"], semantic_rows)
    write_csv(paths["fieldSummary"], summary_rows)
    write_csv(paths["correlations"], correlation_rows)
    write_csv(paths["top"], top_rows)
    write_csv(paths["audit"], audit_rows)
    write_csv(paths["embeddings"], embedding_manifest)
    paths["summary"].write_text(
        render_summary(metadata, summary_rows, correlation_rows, top_rows),
        encoding="utf-8",
    )
    return [paths[key] for key in paths]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze within-scenario semantic similarity using fixed sentence "
            "embeddings and cosine similarity."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIRECTORY
    )
    parser.add_argument(
        "--lexical-pairs", type=Path, default=DEFAULT_LEXICAL_PAIRS_PATH
    )
    parser.add_argument(
        "--lexical-audit", type=Path, default=DEFAULT_LEXICAL_AUDIT_PATH
    )
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    parser.add_argument("--expected-prefix-sha256")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Allow Hugging Face network access; default execution is cache-only.",
    )
    arguments = parser.parse_args()
    if arguments.max_lines < 0:
        parser.error("--max-lines cannot be negative")
    if arguments.batch_size < 1:
        parser.error("--batch-size must be positive")
    if arguments.top_k < 0:
        parser.error("--top-k cannot be negative")
    return arguments


def main() -> int:
    arguments = parse_arguments()
    input_path = arguments.input.expanduser().resolve()
    output_directory = arguments.output_dir.expanduser().resolve()
    lexical_pairs_path = arguments.lexical_pairs.expanduser().resolve()
    lexical_audit_path = arguments.lexical_audit.expanduser().resolve()
    for required in (input_path, lexical_pairs_path, lexical_audit_path):
        if not required.is_file():
            print(f"Required input does not exist: {required}")
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
    expected_hash = arguments.expected_prefix_sha256
    if expected_hash is None and default_frozen_request:
        expected_hash = FROZEN_PREFIX_SHA256
    try:
        prefix_verified = verify_prefix_hash(prefix_hash, expected_hash)
    except ValueError as error:
        print(f"Input verification failed: {error}")
        return 1

    generations = [
        record for record in records if get_record_type(record) == "generation"
    ]
    scenario_counts: dict[str, int] = defaultdict(int)
    for record in generations:
        scenario = record.get("scenario")
        scenario_id = (
            str(scenario.get("scenarioId", ""))
            if isinstance(scenario, dict)
            else ""
        )
        scenario_counts[scenario_id] += 1
    if default_frozen_request and prefix_verified:
        if (
            len(generations) != FROZEN_GENERATION_COUNT
            or dict(sorted(scenario_counts.items()))
            != FROZEN_SCENARIO_GENERATION_COUNTS
        ):
            print("Frozen input has unexpected generation/scenario counts.")
            return 1

    generated_lexical_rows = build_within_scenario_field_rows(generations)
    lexical_pairs_hash = _sha256_file(lexical_pairs_path)
    lexical_audit_hash = _sha256_file(lexical_audit_path)
    if default_frozen_request and prefix_verified:
        if lexical_pairs_hash != FROZEN_LEXICAL_PAIRS_SHA256:
            print("Frozen lexical pair manifest SHA-256 does not match.")
            return 1
        if lexical_audit_hash != FROZEN_LEXICAL_AUDIT_SHA256:
            print("Frozen lexical audit SHA-256 does not match.")
            return 1
    persisted_lexical_rows = _read_csv(lexical_pairs_path)
    lexical_audit_rows = _read_csv(lexical_audit_path)
    if (
        default_frozen_request
        and len(lexical_audit_rows) != FROZEN_AUDIT_PAIR_COUNT
    ):
        print("Frozen lexical audit does not contain exactly 40 pairs.")
        return 1
    try:
        validate_lexical_manifest(
            generated_lexical_rows, persisted_lexical_rows
        )
        identity_rows = collect_text_identities(persisted_lexical_rows)
    except ValueError as error:
        print(f"Lexical alignment failed: {error}")
        return 1

    if not arguments.allow_download:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    try:
        import huggingface_hub
        import numpy
        import sentence_transformers
        import tokenizers
        import torch
        import transformers
        from huggingface_hub.constants import HF_HUB_CACHE
        from sentence_transformers import SentenceTransformer
    except ImportError as error:
        print(
            "Semantic dependencies are missing. Install "
            "Backend/requirements-semantic.txt first: "
            f"{error}"
        )
        return 1

    torch.manual_seed(0)
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    torch.use_deterministic_algorithms(True, warn_only=False)
    try:
        model = SentenceTransformer(
            DEFAULT_MODEL_ID,
            revision=DEFAULT_MODEL_REVISION,
            device="cpu",
            trust_remote_code=False,
            local_files_only=not arguments.allow_download,
        )
    except Exception as error:
        print(f"Embedding model could not be loaded: {type(error).__name__}: {error}")
        return 1
    model.eval()
    embeddings, diagnostics = encode_identities(
        model, identity_rows, arguments.batch_size
    )
    semantic_rows = build_semantic_rows(
        persisted_lexical_rows, embeddings, diagnostics
    )
    summary_rows = build_summary_rows(semantic_rows)
    correlation_rows = build_correlation_rows(semantic_rows)
    top_rows = build_top_rows(semantic_rows, arguments.top_k)
    try:
        enriched_audit = enrich_audit_rows(
            lexical_audit_rows, semantic_rows
        )
    except ValueError as error:
        print(f"Audit alignment failed: {error}")
        return 1
    embedding_manifest = build_embedding_manifest(identity_rows, diagnostics)

    pair_keys = {pair_join_key(row) for row in semantic_rows}
    snapshot_path = (
        Path(HF_HUB_CACHE)
        / ("models--" + DEFAULT_MODEL_ID.replace("/", "--"))
        / "snapshots"
        / DEFAULT_MODEL_REVISION
    )
    if not snapshot_path.is_dir():
        print(f"Resolved model snapshot is missing: {snapshot_path}")
        return 1
    snapshot_hash, snapshot_files = _snapshot_fingerprint(snapshot_path)
    max_wordpieces = max(
        int(row["wordpieces"]) for row in embedding_manifest
    )
    truncated_count = sum(
        bool(row["wouldTruncate"]) for row in embedding_manifest
    )
    metadata = {
        "semanticMetricVersion": SEMANTIC_METRIC_VERSION,
        "analyzerSha256": _sha256_file(Path(__file__).resolve()),
        "lexicalAnalyzerSha256": _sha256_file(
            BACKEND_DIRECTORY / "analyze_lexical_similarity.py"
        ),
        "inputPath": str(input_path),
        "linesRead": lines_read,
        "parsedJsonObjectRecords": len(records),
        "malformedRecords": len(errors),
        "loadErrors": errors,
        "inputPrefixSha256": prefix_hash,
        "expectedInputPrefixSha256": expected_hash,
        "inputPrefixHashVerified": prefix_verified,
        "generationRecords": len(generations),
        "scenarioCount": len(scenario_counts),
        "scenarioGenerationCounts": dict(sorted(scenario_counts.items())),
        "withinScenarioPairs": len(pair_keys),
        "fieldComparisons": len(semantic_rows),
        "fields": list(LEXICAL_FIELDS),
        "lexicalPairsPath": str(lexical_pairs_path),
        "lexicalPairsSha256": lexical_pairs_hash,
        "lexicalAuditPath": str(lexical_audit_path),
        "lexicalAuditSha256": lexical_audit_hash,
        "auditPairs": len(enriched_audit),
        "modelId": DEFAULT_MODEL_ID,
        "modelRevision": DEFAULT_MODEL_REVISION,
        "modelSnapshotPath": str(snapshot_path),
        "modelSnapshotSha256": snapshot_hash,
        "modelSnapshotFiles": snapshot_files,
        "embeddingDimension": int(model.get_embedding_dimension()),
        "pooling": "model-defined mean pooling followed by L2 normalization",
        "modelMaxSequenceLength": int(model.max_seq_length),
        "maximumObservedWordpieces": max_wordpieces,
        "truncatedTextCount": truncated_count,
        "uniqueEmbeddedTexts": len(identity_rows),
        "semanticPreprocessing": (
            "collapse whitespace only; preserve case, punctuation, stopwords, "
            "and word forms"
        ),
        "normalizeEmbeddings": True,
        "cosineImplementation": (
            "dot product of L2-normalized float32 embeddings"
        ),
        "device": "cpu",
        "dtype": "float32",
        "batchSize": arguments.batch_size,
        "deterministicAlgorithms": True,
        "pythonVersion": platform.python_version(),
        "sentenceTransformersVersion": sentence_transformers.__version__,
        "transformersVersion": transformers.__version__,
        "torchVersion": torch.__version__,
        "numpyVersion": numpy.__version__,
        "tokenizersVersion": tokenizers.__version__,
        "huggingfaceHubVersion": huggingface_hub.__version__,
        "offlineModelLoad": not arguments.allow_download,
        "topK": arguments.top_k,
        "p90Method": "linear interpolation at position (n - 1) * 0.90",
        "correlationPValuesReported": False,
    }
    paths = write_outputs(
        output_directory,
        metadata,
        semantic_rows,
        summary_rows,
        correlation_rows,
        top_rows,
        enriched_audit,
        embedding_manifest,
    )
    print(
        f"Analyzed {len(generations)} generations, {len(pair_keys)} "
        f"within-scenario pairs, {len(semantic_rows)} field rows, and "
        f"{len(identity_rows)} unique embedded texts."
    )
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

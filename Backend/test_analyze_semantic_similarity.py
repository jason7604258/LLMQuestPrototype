"""Tests for the frozen within-scenario semantic analysis."""

import csv
import unittest

from analyze_experiments import get_record_type
from analyze_lexical_similarity import (
    DEFAULT_INPUT_PATH,
    DEFAULT_MAX_LINES,
    FROZEN_GENERATION_COUNT,
    build_within_scenario_field_rows,
    load_jsonl_prefix,
)
from analyze_semantic_similarity import (
    DEFAULT_LEXICAL_AUDIT_PATH,
    DEFAULT_LEXICAL_PAIRS_PATH,
    _pearson,
    _spearman,
    build_semantic_rows,
    build_summary_rows,
    collect_text_identities,
    cosine_from_normalized,
    enrich_audit_rows,
    pair_join_key,
    semantic_text,
    validate_lexical_manifest,
)


# mirrors a saved lexical csv row, including values read back as strings
def lexical_row(field: str, request_a: str = "a", request_b: str = "b") -> dict:
    return {
        "comparisonScope": "within_scenario",
        "scenarioId": "scenario-1",
        "field": field,
        "requestIdA": request_a,
        "requestIdB": request_b,
        "titleA": "Title A",
        "titleB": "Title B",
        "textA": "A red flame waits.",
        "textB": "A blue flame waits.",
        "word1gramJaccard": "0.6",
        "tokenLcsF1": "0.75",
        "word3gramJaccard": "0.0",
        "exactNormalizedText": "False",
    }


# checks semantic analysis with small known vectors instead of loading a model
class SemanticMetricTests(unittest.TestCase):
    def test_semantic_preprocessing_only_collapses_whitespace(self):
        # case and punctuation remain while repeated whitespace is collapsed
        self.assertEqual(
            semantic_text("  The  FLAME,\nwaits!  "),
            "The FLAME, waits!",
        )

    def test_cosine_uses_normalized_vectors_and_clamps_roundoff(self):
        self.assertAlmostEqual(cosine_from_normalized([1, 0], [1, 0]), 1.0)
        self.assertAlmostEqual(cosine_from_normalized([1, 0], [0, 1]), 0.0)
        self.assertAlmostEqual(cosine_from_normalized([1, 0], [-1, 0]), -1.0)
        with self.assertRaisesRegex(ValueError, "dimensions"):
            cosine_from_normalized([1, 0], [1])

    def test_manifest_validation_is_order_and_text_sensitive(self):
        rows = [lexical_row("introduction"), lexical_row("completionText")]
        persisted = [dict(row) for row in rows]
        for generated, saved in zip(rows, persisted):
            generated["metricVersion"] = "lexical-field-v3-word"
            generated["exactNormalizedText"] = False
            saved["metricVersion"] = "lexical-field-v3-word"
            saved["exactNormalizedText"] = "False"
        validate_lexical_manifest(rows, persisted)

        # saved rows must keep the same order and text as the regenerated rows
        reversed_rows = list(reversed([dict(row) for row in persisted]))
        with self.assertRaisesRegex(ValueError, "keys/order"):
            validate_lexical_manifest(rows, reversed_rows)

        changed = [dict(row) for row in persisted]
        changed[0]["textA"] = "Different text"
        with self.assertRaisesRegex(ValueError, "textA differs"):
            validate_lexical_manifest(rows, changed)

    def test_each_scenario_field_request_text_is_encoded_once(self):
        rows = [
            lexical_row("introduction", "a", "b"),
            lexical_row("introduction", "a", "c"),
            lexical_row("introduction", "b", "c"),
        ]
        rows[1]["textB"] = "A green flame waits."
        rows[1]["titleB"] = "Title C"
        rows[2]["textA"] = rows[0]["textB"]
        rows[2]["titleA"] = rows[0]["titleB"]
        rows[2]["textB"] = rows[1]["textB"]
        rows[2]["titleB"] = rows[1]["titleB"]

        # shared passages appear in several pairs but need only one encoding
        identities = collect_text_identities(rows)

        self.assertEqual(len(identities), 3)
        self.assertEqual({row["requestId"] for row in identities}, {"a", "b", "c"})

    def test_semantic_rows_keep_lexical_order_and_metrics(self):
        rows = [lexical_row("introduction")]
        # known unit vectors give a cosine of exactly six tenths
        embeddings = {
            ("scenario-1", "introduction", "a"): [1.0, 0.0],
            ("scenario-1", "introduction", "b"): [0.6, 0.8],
        }
        diagnostics = {
            key: {"wordpieces": 5, "wouldTruncate": False}
            for key in embeddings
        }

        semantic_rows = build_semantic_rows(rows, embeddings, diagnostics)

        self.assertEqual(len(semantic_rows), 1)
        self.assertAlmostEqual(semantic_rows[0]["semanticCosine"], 0.6)
        self.assertAlmostEqual(semantic_rows[0]["tokenLcsF1"], 0.75)
        self.assertEqual(semantic_rows[0]["requestIdA"], "a")

    def test_summary_reports_pair_weighted_and_macro_scenario_means(self):
        rows = []
        for field in ("introduction", "completionText"):
            for scenario, value in (("scenario-1", 0.1), ("scenario-2", 0.9)):
                row = lexical_row(field)
                row.update(
                    {
                        "scenarioId": scenario,
                        "semanticCosine": value,
                        "wouldTruncateA": False,
                        "wouldTruncateB": False,
                    }
                )
                rows.append(row)

        summary = build_summary_rows(rows)
        overall = [row for row in summary if row["aggregation"] == "overall_pair_weighted"]

        self.assertEqual(len(overall), 2)
        self.assertTrue(all(row["comparisons"] == 2 for row in overall))
        # equal pair counts make pooled and scenario means coincide in this fixture
        self.assertTrue(all(row["meanSemanticCosine"] == 0.5 for row in overall))
        self.assertTrue(all(row["macroMeanOfScenarioMeans"] == 0.5 for row in overall))
        self.assertTrue(all(abs(row["p90SemanticCosine"] - 0.82) < 1e-12 for row in overall))

    def test_correlations_use_average_ranks_for_ties(self):
        self.assertAlmostEqual(_pearson([1, 2, 3], [2, 4, 6]), 1.0)
        # both tied groups receive average ranks before their correlation is computed
        self.assertAlmostEqual(_spearman([1, 1, 3], [4, 4, 9]), 1.0)
        self.assertAlmostEqual(_spearman([1, 2, 3], [9, 4, 1]), -1.0)

    def test_audit_enrichment_preserves_existing_order(self):
        semantic_rows = []
        audit_rows = []
        for request_a, request_b, base in (("a", "b", 0.2), ("a", "c", 0.4)):
            audit_rows.append(
                {
                    "scenarioId": "scenario-1",
                    "requestIdA": request_a,
                    "requestIdB": request_b,
                    "auditMarker": f"{request_a}-{request_b}",
                }
            )
            for field, offset in (("introduction", 0.0), ("completionText", 0.1)):
                row = lexical_row(field, request_a, request_b)
                row["semanticCosine"] = base + offset
                semantic_rows.append(row)

        enriched = enrich_audit_rows(audit_rows, semantic_rows)

        self.assertEqual([row["auditMarker"] for row in enriched], ["a-b", "a-c"])
        self.assertAlmostEqual(enriched[0]["introductionSemanticCosine"], 0.2)
        self.assertAlmostEqual(enriched[0]["completionSemanticCosine"], 0.3)


# checks saved lexical evidence without making model requests or computing embeddings
class FrozenSemanticIntegrationTests(unittest.TestCase):
    def test_frozen_lexical_manifest_and_audit_have_expected_semantic_scope(self):
        records, errors, lines_read, _ = load_jsonl_prefix(
            DEFAULT_INPUT_PATH, DEFAULT_MAX_LINES
        )
        generations = [
            record for record in records if get_record_type(record) == "generation"
        ]
        generated = build_within_scenario_field_rows(generations)
        with DEFAULT_LEXICAL_PAIRS_PATH.open(encoding="utf-8", newline="") as source:
            persisted = list(csv.DictReader(source))
        with DEFAULT_LEXICAL_AUDIT_PATH.open(encoding="utf-8", newline="") as source:
            audit = list(csv.DictReader(source))

        validate_lexical_manifest(generated, persisted)
        identities = collect_text_identities(persisted)

        self.assertEqual(errors, [])
        self.assertEqual(lines_read, DEFAULT_MAX_LINES)
        self.assertEqual(len(generations), FROZEN_GENERATION_COUNT)
        # each narrative pair contributes separate introduction and completion rows
        self.assertEqual(len(persisted), 592)
        self.assertEqual(len({pair_join_key(row) for row in persisted}), 296)
        self.assertEqual(len(identities), 144)
        self.assertEqual(len(audit), 40)


if __name__ == "__main__":
    unittest.main()

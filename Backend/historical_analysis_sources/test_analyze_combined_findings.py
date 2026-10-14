"""Tests for the frozen lexical–semantic combined findings."""

import unittest

from analyze_combined_findings import (
    CORRELATIONS_PATH,
    GENERATIONS_PATH,
    LEXICAL_AUDIT_PATH,
    LEXICAL_METADATA_PATH,
    LEXICAL_PAIRS_PATH,
    LEXICAL_SUMMARY_PATH,
    SEMANTIC_AUDIT_PATH,
    SEMANTIC_METADATA_PATH,
    SEMANTIC_PAIRS_PATH,
    SEMANTIC_SUMMARY_PATH,
    average_percentiles,
    build_profiles,
    descending_average_ranks,
    expected_audit_hash,
    experiment_context,
    field_key,
    rank_gap_cases,
    read_csv,
    read_json,
    render_report,
    scenario_mean_associations,
    sha256_file,
    validate_sources,
)


class RankHelperTests(unittest.TestCase):
    def test_average_percentiles_use_average_ranks_for_ties(self):
        rows = []
        for index, value in enumerate((0.1, 0.5, 0.5, 0.9)):
            rows.append(
                {
                    "scenarioId": "scenario",
                    "requestIdA": f"a{index}",
                    "requestIdB": f"b{index}",
                    "field": "introduction",
                    "metric": value,
                }
            )

        values = average_percentiles(rows, "metric")

        self.assertAlmostEqual(values[field_key(rows[0])], 0.0)
        self.assertAlmostEqual(values[field_key(rows[1])], 0.5)
        self.assertAlmostEqual(values[field_key(rows[2])], 0.5)
        self.assertAlmostEqual(values[field_key(rows[3])], 1.0)

    def test_descending_ranks_use_average_ranks_for_ties(self):
        ranks = descending_average_ranks({"a": 0.9, "b": 0.5, "c": 0.5})

        self.assertEqual(ranks, {"a": 1.0, "b": 2.5, "c": 2.5})

    def test_audit_hash_is_deterministic_and_uses_no_metric(self):
        row = {
            "sampleSalt": "20260820",
            "scenarioId": "scenario",
            "requestIdA": "a",
            "requestIdB": "b",
            "tokenLcsF1": "0.1",
        }
        first = expected_audit_hash(row)
        row["tokenLcsF1"] = "0.9"

        self.assertEqual(expected_audit_hash(row), first)
        self.assertEqual(len(first), 64)


class FrozenCombinedIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lexical_metadata = read_json(LEXICAL_METADATA_PATH)
        cls.semantic_metadata = read_json(SEMANTIC_METADATA_PATH)
        cls.lexical_summary = read_csv(LEXICAL_SUMMARY_PATH)
        cls.lexical_rows = read_csv(LEXICAL_PAIRS_PATH)
        cls.lexical_audit = read_csv(LEXICAL_AUDIT_PATH)
        cls.semantic_summary = read_csv(SEMANTIC_SUMMARY_PATH)
        cls.semantic_rows = read_csv(SEMANTIC_PAIRS_PATH)
        cls.correlations = read_csv(CORRELATIONS_PATH)
        cls.semantic_audit = read_csv(SEMANTIC_AUDIT_PATH)
        cls.generations = read_csv(GENERATIONS_PATH)

    def test_all_frozen_sources_align(self):
        validate_sources(
            self.lexical_metadata,
            self.semantic_metadata,
            self.lexical_rows,
            self.semantic_rows,
            self.lexical_audit,
            self.semantic_audit,
            self.generations,
        )

        self.assertEqual(len(self.semantic_rows), 592)
        self.assertEqual(len(self.semantic_audit), 40)

    def test_profiles_and_rank_gap_cases_have_expected_shape(self):
        overall, profiles = build_profiles(
            self.lexical_summary, self.semantic_summary
        )
        gaps = rank_gap_cases(self.semantic_rows)
        associations = scenario_mean_associations(profiles)

        self.assertEqual(len(overall), 2)
        self.assertEqual(len(profiles), 16)
        self.assertEqual(set(gaps), {"introduction", "completionText"})
        self.assertEqual(len(associations), 6)
        completion_lcs = next(
            row
            for row in associations
            if row["field"] == "completionText"
            and row["lexicalMetric"] == "tokenLcsF1"
        )
        self.assertAlmostEqual(completion_lcs["spearmanRho"], -1 / 14)
        self.assertTrue(
            all(
                len(direction) == 3
                for field in gaps.values()
                for direction in field.values()
            )
        )
        first = gaps["introduction"]["semanticRankExceedsLcs"][0]
        self.assertEqual(first["requestIdA"], "1ff7bb96e8684e85ab248cdab0727bec")
        self.assertEqual(first["requestIdB"], "c1fa090c646d441295961c69ad3fa2de")

    def test_report_reconciles_key_results(self):
        overall, profiles = build_profiles(
            self.lexical_summary, self.semantic_summary
        )
        gaps = rank_gap_cases(self.semantic_rows)
        associations = scenario_mean_associations(profiles)
        context = experiment_context(self.generations)
        paths = {
            "lexical summary": LEXICAL_SUMMARY_PATH,
            "semantic summary": SEMANTIC_SUMMARY_PATH,
        }
        report = render_report(
            self.lexical_metadata,
            self.semantic_metadata,
            overall,
            profiles,
            self.correlations,
            associations,
            gaps,
            self.semantic_audit,
            context,
            {label: sha256_file(path) for label, path in paths.items()},
        )

        self.assertIn("Introduction semantic cosine exceeds completion in 8/8", report)
        self.assertIn("Completion Token LCS F1 exceeds introduction in 7/8", report)
        self.assertIn("| 72 | 72 | 0 | 72 | 62 | 86.1%", report)
        self.assertIn("not a quality threshold", report)
        self.assertIn("| `completionText` | `tokenLcsF1` | 8 | -0.0714 |", report)


if __name__ == "__main__":
    unittest.main()

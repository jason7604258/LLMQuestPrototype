"""Tests for the reproducible word-level lexical analysis."""

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from analyze_lexical_similarity import (
    _hamilton_allocation,
    build_audit_sample,
    build_summary_rows,
    build_within_scenario_field_rows,
    load_jsonl_prefix,
    token_lcs_f1,
    verify_prefix_hash,
    word_ngram_jaccard,
    word_tokens,
)


# builds the minimum narrative fields needed for lexical comparisons
def generation(
    request_id: str,
    scenario_id: str,
    introduction: str,
    completion_text: str,
) -> dict:
    return {
        "recordType": "generation",
        "requestId": request_id,
        "timestampUtc": "2026-08-20T00:00:00+00:00",
        "scenario": {"scenarioId": scenario_id},
        "narrative": {
            "title": f"Title {request_id}",
            "introduction": introduction,
            "completionText": completion_text,
        },
    }


# checks word metrics, scenario grouping, sampling and fixed source boundaries
class WordMetricTests(unittest.TestCase):
    def test_normalized_word_jaccard_and_lcs_measure_different_properties(self):
        left = word_tokens("Red flame waits.")
        right = word_tokens("Red torch waits.")

        self.assertAlmostEqual(word_ngram_jaccard(left, right, 1), 2 / 4)
        self.assertAlmostEqual(token_lcs_f1(left, right), 4 / 6)
        self.assertEqual(word_ngram_jaccard(left, right, 3), 0.0)

    def test_ngram_jaccard_is_undefined_when_both_texts_are_too_short(self):
        # no triples means an undefined comparison rather than zero overlap
        self.assertIsNone(word_ngram_jaccard(["one"], ["two"], 3))

    def test_only_same_scenario_pairs_are_built_and_fields_stay_separate(self):
        records = [
            generation("a", "scenario-1", "one two three", "four five six"),
            generation("b", "scenario-1", "one two seven", "four eight six"),
            generation("c", "scenario-2", "one two three", "four five six"),
        ]

        rows = build_within_scenario_field_rows(records)

        self.assertEqual(len(rows), 2)
        self.assertEqual({row["scenarioId"] for row in rows}, {"scenario-1"})
        self.assertEqual(
            {row["field"] for row in rows},
            {"introduction", "completionText"},
        )
        summary = build_summary_rows(rows)
        overall = [row for row in summary if row["aggregation"] == "overall"]
        self.assertEqual(len(overall), 2)
        self.assertTrue(all(row["comparisons"] == 1 for row in overall))

    def test_hamilton_allocation_matches_frozen_72_pair_proportions(self):
        # these are available pair counts rather than narrative counts
        sizes = {
            "collect_mushroom_01": 28,
            "kill_torch_01": 36,
            "slay_caveborn_bear_01": 45,
            "slay_caveborn_lizard_01": 45,
            "slay_caveborn_snake_01": 45,
            "slay_caveborn_spider_01": 21,
            "slay_caveborn_turtle_01": 55,
            "slay_torch_boss_01": 21,
        }

        allocation = _hamilton_allocation(sizes, 40)

        self.assertEqual(
            allocation,
            {
                "collect_mushroom_01": 4,
                "kill_torch_01": 5,
                "slay_caveborn_bear_01": 6,
                "slay_caveborn_lizard_01": 6,
                "slay_caveborn_snake_01": 6,
                "slay_caveborn_spider_01": 3,
                "slay_caveborn_turtle_01": 7,
                "slay_torch_boss_01": 3,
            },
        )

    def test_hash_ranked_audit_sample_is_deterministic_and_pair_level(self):
        records = [
            generation(
                f"request-{index}",
                "scenario-1",
                f"intro words number {index}",
                f"completion words number {index}",
            )
            for index in range(5)
        ]
        rows = build_within_scenario_field_rows(records)

        # the same fixed input must select the same unique narrative pairs
        first, allocation = build_audit_sample(rows, 4, "fixed-salt")
        second, _ = build_audit_sample(rows, 4, "fixed-salt")

        self.assertEqual(first, second)
        self.assertEqual(allocation, {"scenario-1": 4})
        self.assertEqual(len(first), 4)
        self.assertEqual(
            len({(row["requestIdA"], row["requestIdB"]) for row in first}),
            4,
        )
        # each sampled pair retains both fields instead of sampling fields separately
        self.assertTrue(
            all("introductionTokenLcsF1" in row for row in first)
        )
        self.assertTrue(
            all("completionTokenLcsF1" in row for row in first)
        )

    def test_prefix_loader_hashes_only_requested_physical_lines(self):
        records = [
            generation("a", "scenario", "one two three", "four five six"),
            generation("b", "scenario", "one two four", "four five seven"),
            generation("c", "scenario", "one two five", "four five eight"),
        ]
        encoded_lines = [
            (json.dumps(record, separators=(",", ":")) + "\n").encode("utf-8")
            for record in records
        ]
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "records.jsonl"
            path.write_bytes(b"".join(encoded_lines))

            # the third physical line must not enter the selected data or its hash
            loaded, errors, lines_read, digest = load_jsonl_prefix(path, 2)

        self.assertEqual(len(loaded), 2)
        self.assertEqual(errors, [])
        self.assertEqual(lines_read, 2)
        self.assertEqual(
            digest, hashlib.sha256(b"".join(encoded_lines[:2])).hexdigest()
        )

    def test_prefix_verification_fails_closed_on_a_mismatch(self):
        actual = "a" * 64

        # letter case is allowed but malformed or mismatched digests are rejected
        self.assertTrue(verify_prefix_hash(actual, actual.upper()))
        self.assertFalse(verify_prefix_hash(actual, None))
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verify_prefix_hash(actual, "b" * 64)
        with self.assertRaisesRegex(ValueError, "64 hex"):
            verify_prefix_hash(actual, "not-a-digest")


if __name__ == "__main__":
    unittest.main()

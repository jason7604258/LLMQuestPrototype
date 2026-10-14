"""Focused offline checks for four-model descriptive aggregation."""

import unittest
from itertools import combinations

from analyze_model_comparison import (
    FIELDS,
    METRICS,
    rank_percentiles,
    summarize,
    validate_rows,
)


# builds distinct synthetic pairs so weighting can be checked without model calls
def pairs(counts, values):
    """Create complete, distinct unordered pairs for both narrative fields."""
    result = []
    for scenario, count in counts.items():
        for field_index, field in enumerate(FIELDS):
            for left, right in combinations(range(count), 2):
                result.append({
                    "comparisonScope": "within_scenario",
                    "scenarioId": scenario,
                    "field": field,
                    "requestIdA": f"{scenario}-{left}",
                    "requestIdB": f"{scenario}-{right}",
                    **{metric: values[scenario] + field_index * 0.1
                       for metric in METRICS},
                })
    return result


class AggregationTests(unittest.TestCase):
    # checks unequal pair counts keep scenario macro distinct from pooled
    def test_unequal_pair_counts_keep_scenario_macro_distinct_from_pooled(self):
        counts = {"small": 2, "large": 3}
        rows = pairs(counts, {"small": 0.2, "large": 0.8})
        scenarios, macros = summarize("Synthetic", rows, counts)
        self.assertEqual(len(scenarios), 4)
        self.assertEqual(len(macros), 2)
        for index, field in enumerate(FIELDS):
            macro = next(row for row in macros if row["field"] == field)
            self.assertEqual(macro["model"], "Synthetic")
            self.assertEqual(macro["scenarios"], 2)
            self.assertEqual(macro["pairs"], 4)
            for metric in METRICS:
                self.assertAlmostEqual(macro[metric], 0.5 + index * 0.1)
                self.assertAlmostEqual(macro["pooled_" + metric], 0.65 + index * 0.1)
                self.assertNotAlmostEqual(macro[metric], macro["pooled_" + metric])
            selected = {row["scenarioId"]: row for row in scenarios
                        if row["field"] == field}
            self.assertEqual(selected["small"]["pairs"], 1)
            self.assertEqual(selected["large"]["pairs"], 3)

    # checks balanced pair counts make macro equal to pooled
    def test_balanced_pair_counts_make_macro_equal_to_pooled(self):
        counts = {"first": 3, "second": 3}
        _, macros = summarize("Balanced", pairs(counts, {"first": 0.2, "second": 0.8}), counts)
        for index, macro in enumerate(macros):
            self.assertEqual(macro["pairs"], 6)
            for metric in METRICS:
                self.assertAlmostEqual(macro[metric], 0.5 + index * 0.1)
                self.assertAlmostEqual(macro[metric], macro["pooled_" + metric])


class RankTests(unittest.TestCase):
    # checks ties use average descending rank percentiles
    def test_ties_use_average_descending_rank_percentiles(self):
        descending_ranks = [2.5, 4, 2.5, 1]
        expected = [(4 - rank) / 3 for rank in descending_ranks]
        self.assertEqual(rank_percentiles([0.3, 0.1, 0.3, 0.9]), expected)

    # checks all ties receive midpoint
    def test_all_ties_receive_midpoint(self):
        self.assertEqual(rank_percentiles([0.4, 0.4, 0.4]), [0.5, 0.5, 0.5])

    # checks undersized rank input is rejected
    def test_undersized_rank_input_is_rejected(self):
        for values in ([], [0.2]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                rank_percentiles(values)


class PairValidationTests(unittest.TestCase):
    # creates fresh synthetic rows for each validation test
    def setUp(self):
        self.counts = {"scenario": 3}
        self.rows = pairs(self.counts, {"scenario": 0.4})

    # checks complete pair coverage is accepted
    def test_complete_pair_coverage_is_accepted(self):
        validate_rows(self.rows, self.counts)

    # checks ordered duplicate is rejected
    def test_ordered_duplicate_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_rows(self.rows + [dict(self.rows[0])], self.counts)

    # checks reversed duplicate cannot replace an unseen pair
    def test_reversed_duplicate_cannot_replace_an_unseen_pair(self):
        changed = [dict(row) for row in self.rows]
        changed[1] = {**changed[0], "requestIdA": changed[0]["requestIdB"],
                      "requestIdB": changed[0]["requestIdA"]}
        with self.assertRaises(ValueError):
            validate_rows(changed, self.counts)

    # checks missing pair is rejected
    def test_missing_pair_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "coverage"):
            validate_rows(self.rows[:-1], self.counts)

    # checks missing blank and nonnumeric metrics are rejected
    def test_missing_blank_and_nonnumeric_metrics_are_rejected(self):
        for metric in METRICS:
            for invalid in (None, "", "not-a-number"):
                changed = [dict(row) for row in self.rows]
                changed[0][metric] = invalid
                with self.subTest(metric=metric, invalid=invalid), self.assertRaises(ValueError):
                    validate_rows(changed, self.counts)
            changed[0].pop(metric)
            with self.subTest(metric=metric, invalid="missing"), self.assertRaises(ValueError):
                validate_rows(changed, self.counts)

    # checks nonfinite metrics are rejected
    def test_nonfinite_metrics_are_rejected(self):
        for metric in METRICS:
            for invalid in (float("nan"), float("inf"), "-inf"):
                changed = [dict(row) for row in self.rows]
                changed[0][metric] = invalid
                with self.subTest(metric=metric, invalid=invalid), self.assertRaisesRegex(ValueError, "Non-finite"):
                    validate_rows(changed, self.counts)

    # checks metric bounds are enforced
    def test_metric_bounds_are_enforced(self):
        for metric in METRICS:
            lower = -1 if metric == "semanticCosine" else 0
            for score in (lower - 0.001, 1.001):
                changed = [dict(row) for row in self.rows]
                changed[0][metric] = score
                with self.subTest(metric=metric, score=score), self.assertRaisesRegex(ValueError, "Out-of-range"):
                    validate_rows(changed, self.counts)
            for score in (lower, 1):
                self.rows[0][metric] = score
                validate_rows(self.rows, self.counts)


if __name__ == "__main__":
    unittest.main()

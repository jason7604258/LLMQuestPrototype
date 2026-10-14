"""checks offline experiment analysis and report output"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from analyze_experiments import (
    analyze_records,
    load_jsonl,
    render_markdown,
    write_outputs,
)


def generation(
    request_id: str,
    title: str,
    source: str = "openai",
    scenario_id: str = "kill_test",
    introduction: str = "Five flame warriors returned to the arena.",
    completion_text: str = "The final flame went dark.",
):
    """builds one story generation record for a test"""

    return {
        "schemaVersion": 2,
        "recordType": "generation",
        "timestampUtc": "2026-08-07T10:00:00+00:00",
        "requestId": request_id,
        "promptVersion": "narrative-wrapper-v1",
        "source": source,
        "model": "test-model",
        "openaiAttempted": True,
        "fallbackReason": None,
        "scenario": {
            "scenarioId": scenario_id,
            "scenarioType": "KillEnemies",
            "requiredAmount": 5,
        },
        "continuity": {"previousStorySummary": "", "wasProvided": False},
        "narrative": {
            "title": title,
            "introduction": introduction,
            "objectiveText": "Defeat 5 warriors.",
            "completionText": completion_text,
            "storySummary": "Five warriors were defeated.",
        },
        "validation": {"returnedNarrativeAccepted": True},
        "performance": {
            "openaiLatencySeconds": 2.0,
            "backendLatencySeconds": 2.5,
        },
        "usage": {
            "inputTokens": 100,
            "outputTokens": 50,
            "totalTokens": 150,
            "estimatedCostUsd": 0.01,
        },
    }


def event(request_id: str, event_type: str, progress: int, elapsed: float):
    """builds one gameplay event record for a test"""

    return {
        "schemaVersion": 2,
        "recordType": "gameplay_event",
        "timestampUtc": "2026-08-07T10:01:00+00:00",
        "requestId": request_id,
        "scenarioId": "kill_test",
        "scenarioType": "KillEnemies",
        "eventType": event_type,
        "completed": event_type == "scenario_completed",
        "elapsedSeconds": elapsed,
        "currentProgress": progress,
        "requiredAmount": 5,
        "narrativeSource": "backend",
        "fallbackReason": None,
        "unityValidation": {
            "backendNarrativeAccepted": True,
            "error": None,
        },
    }


class ExperimentAnalysisTests(unittest.TestCase):
    """checks record loading totals joins and written reports"""

    def test_analysis_joins_lifecycle_and_totals_usage(self):
        """checks joined gameplay totals cost and repeated story text"""

        # the second started run deliberately has no completion record
        records = [
            generation("run-1", "The Last Flame"),
            event("run-1", "scenario_started", 0, 0.0),
            event("run-1", "scenario_completed", 5, 12.0),
            generation("run-2", "The Last Flame"),
            event("run-2", "scenario_started", 0, 0.0),
        ]

        result = analyze_records(records)

        self.assertEqual(result["generation"]["total"], 2)
        self.assertEqual(result["generation"]["openaiSuccesses"], 2)
        self.assertEqual(result["usage"]["totalTokens"], 300)
        self.assertAlmostEqual(result["usage"]["estimatedCostUsd"], 0.02)
        self.assertEqual(result["gameplay"]["started"], 2)
        self.assertEqual(result["gameplay"]["completed"], 1)
        self.assertEqual(result["gameplay"]["completionRate"], 0.5)
        self.assertEqual(result["gameplay"]["startedNotCompleted"], 1)
        self.assertEqual(result["gameplay"]["averageCompletionSeconds"], 12.0)
        self.assertEqual(result["repetition"]["metricVersion"], "lexical-field-v2")
        self.assertEqual(result["repetition"]["totalFieldPairs"], 2)
        self.assertEqual(result["repetition"]["withinScenarioFieldPairs"], 2)
        self.assertEqual(result["repetition"]["exactFieldPairs"], 2)
        self.assertEqual(result["repetition"]["repeatedTitleGroups"], 1)

    def test_introduction_and_completion_are_scored_separately(self):
        """checks that one matching field cannot hide a different field"""

        result = analyze_records(
            [
                generation(
                    "run-1",
                    "First title",
                    introduction="A silver trail crosses the ruined arena.",
                    completion_text="The western gate opens at dawn.",
                ),
                generation(
                    "run-2",
                    "Second title",
                    introduction="A silver trail crosses the ruined arena.",
                    completion_text="Rain settles over the empty forest road.",
                ),
            ]
        )

        pairs_by_field = {
            pair["field"]: pair for pair in result["similarityPairs"]
        }
        self.assertEqual(
            set(pairs_by_field),
            {"introduction", "completionText"},
        )
        self.assertEqual(
            pairs_by_field["introduction"]["similarityBand"],
            "exact",
        )
        self.assertTrue(
            pairs_by_field["introduction"]["exactNormalizedText"]
        )
        self.assertFalse(
            pairs_by_field["completionText"]["exactNormalizedText"]
        )

    def test_title_change_does_not_affect_field_scores(self):
        """checks title is metadata and exact-only rather than fuzzy input"""

        # only fields outside the two scored passages change in this fixture
        second = generation("run-2", "A Road Through Morning Rain")
        second["narrative"]["objectiveText"] = "Defeat a different amount."
        second["narrative"]["storySummary"] = "A different rolling summary."
        result = analyze_records(
            [
                generation("run-1", "Embers Beneath the Arch"),
                second,
            ]
        )

        self.assertEqual(result["repetition"]["exactFieldPairs"], 2)
        self.assertEqual(result["repetition"]["repeatedTitleGroups"], 0)
        self.assertTrue(
            all(
                pair["similarity"] == 1.0
                for pair in result["similarityPairs"]
            )
        )

    def test_within_scenario_is_primary_and_cross_scenario_is_secondary(self):
        """checks pair scope is based on two known scenario identifiers"""

        result = analyze_records(
            [
                generation("run-1", "One", scenario_id="scenario-a"),
                generation("run-2", "Two", scenario_id="scenario-a"),
                generation("run-3", "Three", scenario_id="scenario-b"),
            ]
        )

        self.assertEqual(result["repetition"]["withinScenarioFieldPairs"], 2)
        self.assertEqual(result["repetition"]["crossScenarioFieldPairs"], 4)
        scopes = {
            pair["comparisonScope"] for pair in result["similarityPairs"]
        }
        self.assertEqual(scopes, {"within_scenario", "cross_scenario"})
        self.assertEqual(result["repetition"]["primaryScope"], "within_scenario")
        self.assertEqual(result["repetition"]["secondaryScope"], "cross_scenario")

    def test_missing_narrative_field_is_skipped(self):
        """checks absent text is not treated as similarity or diversity"""

        # missing text removes its comparison rather than creating a zero score
        missing_introduction = generation("run-1", "One")
        missing_introduction["narrative"].pop("introduction")
        result = analyze_records(
            [missing_introduction, generation("run-2", "Two")]
        )

        self.assertEqual(result["repetition"]["totalFieldPairs"], 1)
        self.assertEqual(len(result["similarityPairs"]), 1)
        self.assertEqual(
            result["similarityPairs"][0]["field"],
            "completionText",
        )

    def test_normalization_produces_exact_field_and_title_matches(self):
        """checks NFKC case punctuation and whitespace normalization"""

        result = analyze_records(
            [
                generation(
                    "run-1",
                    "ＴＨＥ Last-Flame!",
                    introduction="ＦＩＶＥ—flames\nreturn.",
                    completion_text="The path is SAFE!",
                ),
                generation(
                    "run-2",
                    "the last flame",
                    introduction="five flames return",
                    completion_text="the path is safe",
                ),
            ]
        )

        self.assertEqual(result["repetition"]["exactFieldPairs"], 2)
        self.assertEqual(result["repetition"]["repeatedTitleGroups"], 1)
        self.assertTrue(
            all(
                pair["exactNormalizedText"]
                for pair in result["similarityPairs"]
            )
        )
        self.assertEqual(
            result["repeatedTitleRows"][0]["normalizedTitle"],
            "the last flame",
        )

    def test_thresholds_validate_and_assign_review_band(self):
        """checks ordered thresholds and inclusive field-level grading"""

        left = generation("run-1", "One", introduction="abc")
        right = generation("run-2", "Two", introduction="abd")
        left["narrative"].pop("completionText")
        right["narrative"].pop("completionText")

        baseline = analyze_records(
            [left, right],
            similarity_threshold=1.0,
            review_threshold=0.0,
        )
        # use the computed score to exercise equality at the chosen threshold
        boundary = baseline["similarityPairs"][0]["similarity"]
        result = analyze_records(
            [left, right],
            similarity_threshold=boundary,
            review_threshold=0.0,
        )

        self.assertEqual(result["repetition"]["highNonExactFieldPairs"], 1)
        self.assertEqual(
            result["similarityPairs"][0]["similarityBand"],
            "high",
        )
        above_boundary = analyze_records(
            [left, right],
            similarity_threshold=boundary + 0.000001,
            review_threshold=0.0,
        )
        self.assertEqual(
            above_boundary["similarityPairs"][0]["similarityBand"],
            "review",
        )
        with self.assertRaises(ValueError):
            analyze_records(
                [left, right],
                similarity_threshold=0.79,
                review_threshold=0.80,
            )

    def test_schema_one_generation_is_supported(self):
        """checks support for an older generation record"""

        old_record = generation("old-run", "Old Story")
        old_record.pop("recordType")
        old_record["schemaVersion"] = 1
        old_record.pop("validation")

        result = analyze_records([old_record])

        self.assertEqual(result["generation"]["total"], 1)
        self.assertEqual(result["generation"]["backendValidationKnown"], 0)

    def test_loader_skips_malformed_lines(self):
        """checks that one bad json line does not hide valid records"""

        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "runs.jsonl"
            path.write_text(
                json.dumps(generation("valid", "Valid"))
                + "\n{broken json\n",
                encoding="utf-8",
            )
            records, errors = load_jsonl(path)

        self.assertEqual(len(records), 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("Line 2", errors[0])

    def test_outputs_include_markdown_and_csv_files(self):
        """checks that every expected report file is written"""

        records = [generation("run-1", "The Last Flame")]
        result = analyze_records(records)

        with TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "reports"
            paths = write_outputs(
                result,
                Path("example.jsonl"),
                output_directory,
            )
            markdown = paths[0].read_text(encoding="utf-8")

            self.assertEqual(len(paths), 6)
            self.assertTrue(all(path.exists() for path in paths))
            self.assertEqual(
                [path.name for path in paths],
                [
                    "experiment_summary.md",
                    "generation_records.csv",
                    "scenario_summary.csv",
                    "similar_narratives.csv",
                    "repeated_titles.csv",
                    "lexical_field_summary.csv",
                ],
            )
            self.assertIn("Generation reliability", markdown)
            self.assertIn("Narrative lexical diversity (field-level v2)", markdown)
            self.assertIn("requestId", paths[1].read_text(encoding="utf-8"))
            self.assertIn(
                "comparisonScope",
                paths[3].read_text(encoding="utf-8"),
            )
            self.assertIn(
                "normalizedTitle",
                paths[4].read_text(encoding="utf-8"),
            )
            self.assertIn(
                "aggregation",
                paths[5].read_text(encoding="utf-8"),
            )

    def test_markdown_explains_primary_scope_and_exact_only_titles(self):
        """checks report readers can distinguish primary and title measures"""

        result = analyze_records(
            [generation("run-1", "Story"), generation("run-2", "Other")]
        )
        markdown = render_markdown(result, Path("runs.jsonl"))

        self.assertIn(
            "Primary analysis: compare `introduction` and `completionText`",
            markdown,
        )
        self.assertIn("Title: exact normalized repetition only", markdown)
        self.assertIn("Primary within-scenario results", markdown)

    def test_markdown_explains_missing_gameplay_data(self):
        """checks clear report text when gameplay events are missing"""

        result = analyze_records([generation("run-1", "Story")])
        markdown = render_markdown(result, Path("runs.jsonl"))

        self.assertIn("Completion rate: N/A", markdown)


if __name__ == "__main__":
    # runs these tests when this file is started directly
    unittest.main()

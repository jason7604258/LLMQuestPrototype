"""Tests for fixed cohort validation; never call a model or change real data."""

import copy
import tempfile
import unittest
from pathlib import Path

import run_model_analysis as runner


def complete_fixture():
    counts = {s: 9 for s in runner.SCENARIOS}
    records = []
    previous = ""
    for i in range(72):
        scenario = list(counts)[i % 8]
        request = f"request-{i:02d}"
        summary = f"completed story {i}"
        generation = {
            "recordType": "generation", "requestId": request, "model": "test-model",
            "source": "openai", "openaiAttempted": True, "modelOutput": {"accepted": True},
            "validation": {"returnedNarrativeAccepted": True},
            "scenario": {"scenarioId": scenario},
            "narrative": {"introduction": "three words here", "completionText": "three more words",
                          "storySummary": summary},
            "continuity": {"previousStorySummary": previous, "wasProvided": bool(previous)},
        }
        records.append(generation)
        for event in ("scenario_started", "scenario_completed"):
            records.append({"recordType": "gameplay_event", "requestId": request,
                            "scenarioId": scenario, "eventType": event,
                            "completed": event == "scenario_completed", "narrativeSource": "backend",
                            "unityValidation": {"backendNarrativeAccepted": True}})
        previous = summary
    return records, counts


class CohortTests(unittest.TestCase):
    def test_complete_cohort(self):
        records, counts = complete_fixture()
        self.assertEqual(len(runner.validate_generations(records, "test-model", counts, True)), 72)

    def test_late_completion_post_does_not_break_summary_chain(self):
        records, counts = complete_fixture()
        records[2], records[3] = records[3], records[2]
        self.assertEqual(len(runner.validate_generations(records, "test-model", counts, True)), 72)

    def test_wrong_requested_model_is_not_silently_filtered(self):
        records, counts = complete_fixture()
        records[3]["model"] = "wrong"
        with self.assertRaisesRegex(ValueError, "unexpected model"):
            runner.validate_generations(records, "test-model", counts, True)

    def test_fallback_is_not_silently_filtered(self):
        records, counts = complete_fixture()
        records[3]["source"] = "fallback"
        with self.assertRaisesRegex(ValueError, "fallback"):
            runner.validate_generations(records, "test-model", counts, True)

    def test_context_mismatch_rejected(self):
        records, counts = complete_fixture()
        records[3]["continuity"]["previousStorySummary"] = "another model's old story"
        with self.assertRaisesRegex(ValueError, "continuity mismatch"):
            runner.validate_generations(records, "test-model", counts, True)

    def test_missing_completion_rejected(self):
        records, counts = complete_fixture()
        records.pop()
        with self.assertRaisesRegex(ValueError, "completion count"):
            runner.validate_generations(records, "test-model", counts, True)

    def test_duplicate_request_rejected(self):
        records, counts = complete_fixture()
        records[3] = copy.deepcopy(records[0])
        with self.assertRaisesRegex(ValueError, "duplicate request"):
            runner.validate_generations(records, "test-model", counts, True)

    def test_frozen_artifact_cannot_be_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.jsonl"
            runner.save_frozen(path, b"same")
            runner.save_frozen(path, b"same")
            with self.assertRaisesRegex(ValueError, "differs"):
                runner.save_frozen(path, b"changed")
            self.assertEqual(path.read_bytes(), b"same")

    def test_reject_original_output_directory(self):
        with self.assertRaisesRegex(ValueError, "protected"):
            runner.check_output_directory(runner.BACKEND / "reports/semantic_frozen72_v1")

    def test_reject_output_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "redirect").symlink_to(runner.BACKEND / "reports/semantic_frozen72_v1", target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                runner.check_output_directory(root)


if __name__ == "__main__":
    unittest.main()

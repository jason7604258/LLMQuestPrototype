"""check relocated saved-score reproduction and its source/output boundaries"""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]


class PortableComparisonTests(unittest.TestCase):
    # each test gets a relocated copy containing only the required analysis evidence
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "relocated_project"
        backend = self.root / "Backend"
        backend.mkdir(parents=True)
        for name in ("analyze_experiments.py", "analyze_lexical_similarity.py",
                     "analyze_semantic_similarity.py", "run_model_analysis.py",
                     "analyze_model_comparison.py"):
            shutil.copyfile(PROJECT / "Backend" / name, backend / name)
        shutil.copytree(PROJECT / "Backend" / "historical_analysis_sources",
                        backend / "historical_analysis_sources")
        (backend / "logs").mkdir()
        for name in ("demo_narrative_runs_2026-08-20_take01.jsonl",
                     "terra_gameplay_run01.jsonl", "luna_gameplay_run01.jsonl",
                     "astra_gameplay_run01.jsonl"):
            shutil.copyfile(PROJECT / "Backend" / "logs" / name, backend / "logs" / name)
        for name in ("lexical_frozen72_v3", "semantic_frozen72_v1", "model_comparison_v1"):
            shutil.copytree(PROJECT / "Backend" / "reports" / name,
                            backend / "reports" / name)
        (self.root / "Tools").mkdir()
        shutil.copyfile(PROJECT / "Tools" / "reproduce_saved_comparison.py",
                        self.root / "Tools" / "reproduce_saved_comparison.py")
        changes = PROJECT / "Docs" / "PACKAGING_CHANGES.json"
        if changes.is_file():
            (self.root / "Docs").mkdir()
            shutil.copyfile(changes, self.root / "Docs" / changes.name)

    # run the copied helper as a fresh process to avoid imported original-project paths
    def run_helper(self, *arguments):
        return subprocess.run(
            [sys.executable, "Tools/reproduce_saved_comparison.py", *arguments],
            cwd=self.root, capture_output=True, text=True, check=False)

    # relocation must preserve every calculated csv and leave reference inputs untouched
    def test_relocated_reproduction_matches_all_saved_tables(self):
        reference = self.root / "Backend" / "reports" / "model_comparison_v1"
        before = {p: p.read_bytes() for p in (self.root / "Backend").rglob("*") if p.is_file()}
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.root / "ReproducedReports" / "saved_comparison"
        for name in ("scenario_comparison.csv", "model_macro_summary.csv",
                     "pair_correlations.csv", "metric_disagreement_cases.csv"):
            self.assertEqual((output / name).read_bytes(), (reference / name).read_bytes())
        for path, contents in before.items():
            self.assertEqual(path.read_bytes(), contents, str(path))
        self.assertIn("No model was loaded", result.stdout)

    # a changed score file must fail before producing a misleading new report
    def test_modified_saved_pair_file_is_rejected(self):
        path = self.root / "Backend/reports/model_comparison_v1/terra/semantic/within_scenario_semantic_pairs.csv"
        path.write_bytes(path.read_bytes() + b"\n")
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Hash mismatch", result.stderr)
        self.assertFalse((self.root / "ReproducedReports" / "saved_comparison").exists())

    # comments are allowed but changing the active algorithm must not pass the source check
    def test_changed_documented_algorithm_is_rejected(self):
        path = self.root / "Backend" / "analyze_model_comparison.py"
        path.write_text(path.read_text() + "\nUNRECORDED_CHANGE = True\n")
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Documented source changed behaviour", result.stderr)

    # a second run needs a new destination instead of overwriting an earlier result
    def test_existing_output_directory_is_rejected(self):
        output = self.root / "ReproducedReports" / "saved_comparison"
        output.mkdir(parents=True)
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)

    # no derived output may be created under the retained backend evidence
    def test_protected_output_directory_is_rejected(self):
        result = self.run_helper("--output-dir", "Backend/reports/new_run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside Backend", result.stderr)

    # a redacted file is accepted only when its packaged bytes match the recorded mapping
    def test_unrecorded_metadata_change_is_rejected(self):
        path = self.root / "Backend/reports/semantic_frozen72_v1/analysis_metadata.json"
        path.write_bytes(path.read_bytes() + b"\n")
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Hash mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()

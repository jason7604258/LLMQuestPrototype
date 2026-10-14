"""checks backend requests fallbacks validation and experiment logs"""

import json
import os
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import (
    build_system_prompt,
    build_user_prompt,
    create_server,
    generate_fallback_narrative,
    generate_narrative,
    generate_narrative_with_openai,
    save_run_record,
    validate_generated_narrative,
)


# complete valid request reused by backend tests
VALID_REQUEST = {
    "scenarioId": "kill_torch_01",
    "scenarioType": "KillEnemies",
    "targetId": "enemy_torch",
    "requiredAmount": 5,
    "targetVisualDescription": (
        "A humanoid warrior carrying a burning torch."
    ),
    "targetAbilityDescription": (
        "It chases the player and attacks at close range."
    ),
    "mapDescription": (
        "An abandoned outdoor arena surrounded by mountains."
    ),
    "previousStorySummary": "",
    "tone": (
        "Accessible open-air adventure fantasy with a hopeful sense of "
        "exploration. Use concise, clear language and vivid natural imagery."
    ),
}


class NarrativeBackendTests(unittest.TestCase):
    """checks backend helpers and live local http routes"""

    @classmethod
    def setUpClass(cls) -> None:
        """starts one local server shared by all tests"""

        # port zero lets the system choose a free local port
        cls.server = create_server("127.0.0.1", 0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True,
        )
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        """stops the shared local server after all tests"""

        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_health_endpoint(self) -> None:
        """checks health status and fallback mode without an api key"""

        with patch.dict(os.environ, {}, clear=True):
            with urlopen(f"http://127.0.0.1:{self.port}/health") as response:
                payload = json.load(response)

        self.assertEqual(response.status, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["mode"], "fixed-fallback")
        self.assertEqual(payload["maxPreviousStorySummaryLength"], 300)

    def test_generate_narrative(self) -> None:
        """checks fallback response and its saved generation record"""

        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "runs.jsonl"
            request = Request(
                f"http://127.0.0.1:{self.port}/generate-narrative",
                data=json.dumps(VALID_REQUEST).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with patch.dict(
                os.environ,
                {"NARRATIVE_LOG_PATH": str(log_path)},
                clear=True,
            ):
                with urlopen(request) as response:
                    payload = json.load(response)

            records = [
                json.loads(line)
                for line in log_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(response.status, 200)
        self.assertEqual(payload["title"], "Torches on the Old Road")
        self.assertEqual(
            payload["targetDisplayNamePlural"],
            "Torch Guards",
        )
        self.assertEqual(len(payload), 7)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["schemaVersion"], 2)
        self.assertEqual(records[0]["recordType"], "generation")
        self.assertEqual(
            records[0]["promptVersion"],
            "narrative-wrapper-v4",
        )
        self.assertEqual(records[0]["source"], "fallback")
        self.assertFalse(records[0]["openaiAttempted"])
        self.assertEqual(records[0]["scenario"]["requiredAmount"], 5)
        self.assertEqual(records[0]["narrative"], payload)
        self.assertNotIn("OPENAI_API_KEY", json.dumps(records[0]))

    def test_gameplay_events_are_joinable_with_generation(self) -> None:
        """checks generation start and completion share one request id"""

        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "runs.jsonl"
            request_payload = dict(VALID_REQUEST)
            request_payload["requestId"] = "joined-run-001"
            generation_request = Request(
                f"http://127.0.0.1:{self.port}/generate-narrative",
                data=json.dumps(request_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            started_event = {
                "requestId": "joined-run-001",
                "scenarioId": "kill_torch_01",
                "scenarioType": "KillEnemies",
                "eventType": "scenario_started",
                "completed": False,
                "elapsedSeconds": 0.0,
                "currentProgress": 0,
                "requiredAmount": 5,
                "narrativeSource": "backend",
                "backendNarrativeAcceptedByUnity": True,
                "unityValidationError": "",
                "fallbackReason": "",
            }
            completed_event = dict(started_event)
            completed_event.update(
                {
                    "eventType": "scenario_completed",
                    "completed": True,
                    "elapsedSeconds": 12.75,
                    "currentProgress": 5,
                }
            )

            with patch.dict(
                os.environ,
                {"NARRATIVE_LOG_PATH": str(log_path)},
                clear=True,
            ):
                with urlopen(generation_request) as response:
                    self.assertEqual(response.status, 200)

                for event_payload in (started_event, completed_event):
                    event_request = Request(
                        f"http://127.0.0.1:{self.port}/record-run-event",
                        data=json.dumps(event_payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urlopen(event_request) as response:
                        self.assertEqual(response.status, 200)

            records = [
                json.loads(line)
                for line in log_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(len(records), 3)
        self.assertEqual(
            {record["requestId"] for record in records},
            {"joined-run-001"},
        )
        self.assertEqual(
            [record["recordType"] for record in records],
            ["generation", "gameplay_event", "gameplay_event"],
        )
        self.assertEqual(records[1]["eventType"], "scenario_started")
        self.assertFalse(records[1]["completed"])
        self.assertEqual(records[2]["eventType"], "scenario_completed")
        self.assertTrue(records[2]["completed"])
        self.assertEqual(records[2]["elapsedSeconds"], 12.75)
        self.assertTrue(
            records[2]["unityValidation"]["backendNarrativeAccepted"]
        )

    def test_uses_openai_result_when_key_is_configured(self) -> None:
        """checks that an api key selects the openai story result"""

        generated = generate_fallback_narrative(VALID_REQUEST)
        generated["title"] = "A New LLM Narrative"

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "test-model"},
            clear=True,
        ):
            with patch(
                "app.generate_narrative_with_openai",
                return_value=generated,
            ) as mocked_generator:
                result = generate_narrative(VALID_REQUEST)

        self.assertEqual(result["title"], "A New LLM Narrative")
        mocked_generator.assert_called_once_with(
            VALID_REQUEST,
            "test-key",
            "test-model",
        )

    def test_openai_result_populates_experiment_metrics(self) -> None:
        """checks openai source timing and usage metrics"""

        generated = generate_fallback_narrative(VALID_REQUEST)
        generated["title"] = "A Measured LLM Narrative"
        metrics = {}
        usage = {
            "inputTokens": 405,
            "outputTokens": 120,
            "totalTokens": 525,
            "estimatedCostUsd": 0.005625,
        }

        def fake_openai_generation(
            _payload,
            _api_key,
            _model,
            run_metrics,
        ):
            """returns fixed text while filling expected openai metrics"""

            run_metrics["openaiLatencySeconds"] = 5.32
            run_metrics["usage"] = usage
            return generated

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "test-model"},
            clear=True,
        ):
            with patch(
                "app.generate_narrative_with_openai",
                side_effect=fake_openai_generation,
            ):
                result = generate_narrative(VALID_REQUEST, metrics)

        self.assertEqual(result["title"], "A Measured LLM Narrative")
        self.assertEqual(metrics["source"], "openai")
        self.assertTrue(metrics["openaiAttempted"])
        self.assertIsNone(metrics["fallbackReason"])
        self.assertEqual(metrics["openaiLatencySeconds"], 5.32)
        self.assertEqual(metrics["usage"], usage)

    def test_openai_failure_uses_fallback(self) -> None:
        """checks that an openai error returns safe fallback text"""

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key"},
            clear=True,
        ):
            with patch(
                "app.generate_narrative_with_openai",
                side_effect=RuntimeError("simulated failure"),
            ):
                result = generate_narrative(VALID_REQUEST)

        self.assertEqual(result["title"], "Torches on the Old Road")

    def test_collect_fallback_matches_collect_scenario(self) -> None:
        """checks collection fallback amount wording and fields"""

        request_payload = dict(VALID_REQUEST)
        request_payload.update(
            {
                "scenarioId": "collect_mushroom_01",
                "scenarioType": "CollectItems",
                "targetId": "item_mushroom",
                "requiredAmount": 3,
            }
        )

        narrative = generate_fallback_narrative(request_payload)

        self.assertEqual(narrative["title"], "Glowcaps Among the Grass")
        self.assertIn("3", narrative["objectiveText"])
        self.assertIn("Gather", narrative["objectiveText"])
        validate_generated_narrative(narrative, request_payload)

    def test_boss_fallback_matches_boss_scenario(self) -> None:
        """checks boss fallback amount wording and fields"""

        request_payload = dict(VALID_REQUEST)
        request_payload.update(
            {
                "scenarioId": "slay_torch_boss_01",
                "scenarioType": "SlayBoss",
                "targetId": "boss_torch_warden",
                "requiredAmount": 1,
            }
        )

        narrative = generate_fallback_narrative(request_payload)

        self.assertEqual(
            narrative["title"],
            "The Guardian of the Mountain Arena",
        )
        self.assertIn("1", narrative["objectiveText"])
        self.assertIn("Warden", narrative["targetDisplayNameSingular"])
        validate_generated_narrative(narrative, request_payload)

    def test_kill_fallback_matches_each_caveborn_target(self) -> None:
        """checks fallback text for every caveborn enemy id"""

        targets = {
            "enemy_caveborn_bear": (
                "Claw Marks by the Old Road",
                "Caveborn Bear",
            ),
            "enemy_caveborn_lizard": (
                "Bright Crests in the Grass",
                "Caveborn Lizard",
            ),
            "enemy_caveborn_spider": (
                "Webs Between the Ruins",
                "Caveborn Spider",
            ),
            "enemy_caveborn_snake": (
                "Tracks in the Warm Grass",
                "Caveborn Snake",
            ),
            "enemy_caveborn_turtle": (
                "The Shell Beside the Ruins",
                "Caveborn Turtle",
            ),
        }

        for target_id, expected in targets.items():
            with self.subTest(target_id=target_id):
                request_payload = dict(VALID_REQUEST)
                request_payload.update(
                    {
                        "scenarioId": f"test_{target_id}",
                        "targetId": target_id,
                        "requiredAmount": 2,
                    }
                )

                narrative = generate_fallback_narrative(request_payload)

                self.assertEqual(narrative["title"], expected[0])
                self.assertEqual(
                    narrative["targetDisplayNameSingular"],
                    expected[1],
                )
                self.assertNotIn("Torchbearer", json.dumps(narrative))
                validate_generated_narrative(narrative, request_payload)

    def test_unknown_kill_target_uses_neutral_fallback(self) -> None:
        """checks neutral fallback text for a new enemy id"""

        request_payload = dict(VALID_REQUEST)
        request_payload["targetId"] = "enemy_future_creature"

        narrative = generate_fallback_narrative(request_payload)

        self.assertEqual(
            narrative["targetDisplayNameSingular"],
            "Wild Creature",
        )
        self.assertNotIn("Torch Guard", json.dumps(narrative))
        validate_generated_narrative(narrative, request_payload)

    def test_concurrent_experiment_writes_remain_valid_jsonl(self) -> None:
        """checks that several log writes stay as separate json lines"""

        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "runs.jsonl"
            records = [
                {"requestId": f"concurrent-{index}", "index": index}
                for index in range(12)
            ]

            with patch.dict(
                os.environ,
                {"NARRATIVE_LOG_PATH": str(log_path)},
                clear=True,
            ):
                # simultaneous writers must not interleave parts of json records
                threads = [
                    threading.Thread(
                        target=save_run_record,
                        args=(record,),
                    )
                    for record in records
                ]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join(timeout=2)

            saved_records = [
                json.loads(line)
                for line in log_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(len(saved_records), len(records))
        self.assertEqual(
            {record["requestId"] for record in saved_records},
            {record["requestId"] for record in records},
        )

    def test_structured_openai_sdk_path(self) -> None:
        """checks parsed openai output token usage and client settings"""

        generated = generate_fallback_narrative(VALID_REQUEST)
        parsed_output = MagicMock()
        parsed_output.model_dump.return_value = generated

        # the fake response supplies usage without contacting the model service
        sdk_response = MagicMock()
        sdk_response.output_parsed = parsed_output
        sdk_response.usage = SimpleNamespace(
            input_tokens=405,
            input_tokens_details=SimpleNamespace(
                cached_tokens=0,
                cache_write_tokens=0,
            ),
            output_tokens=120,
            total_tokens=525,
        )
        sdk_client = MagicMock()
        sdk_client.responses.parse.return_value = sdk_response

        # replace the client itself so the sdk path stays local
        with patch("openai.OpenAI", return_value=sdk_client) as openai_class:
            with patch("builtins.print") as mocked_print:
                result = generate_narrative_with_openai(
                    VALID_REQUEST,
                    "test-key",
                    "test-model",
                )

        self.assertEqual(result, generated)
        openai_class.assert_called_once_with(
            api_key="test-key",
            timeout=20.0,
            max_retries=1,
        )
        parse_arguments = sdk_client.responses.parse.call_args.kwargs
        self.assertEqual(parse_arguments["model"], "test-model")
        self.assertEqual(len(parse_arguments["input"]), 2)
        self.assertIn("text_format", parse_arguments)
        printed_messages = [
            call.args[0] for call in mocked_print.call_args_list
        ]
        self.assertEqual(len(printed_messages), 2)
        self.assertRegex(
            printed_messages[0],
            r"^\[backend\] \[request direct\] OpenAI response received "
            r"in \d+\.\d{2}s\.$",
        )
        self.assertEqual(
            printed_messages[1],
            "[backend] [request direct] Usage model='test-model' "
            "input=405 cached=0 cache_write=0 output=120 total=525 "
            "estimated_cost=unavailable",
        )

    def test_rejects_objective_with_wrong_amount(self) -> None:
        """checks rejection when objective amount is wrong"""

        generated = generate_fallback_narrative(VALID_REQUEST)
        generated["objectiveText"] = "Defeat 8 Ashen Warriors."

        with self.assertRaisesRegex(Exception, "required amount"):
            validate_generated_narrative(generated, VALID_REQUEST)

    def test_rejects_required_amount_embedded_in_another_number(self) -> None:
        """checks rejection when the amount is part of a larger number"""

        generated = generate_fallback_narrative(VALID_REQUEST)
        # the required five must not match the final digit of fifteen
        generated["objectiveText"] = "Defeat 15 Ashen Warriors."

        with self.assertRaisesRegex(Exception, "required amount"):
            validate_generated_narrative(generated, VALID_REQUEST)

    def test_prompt_uses_continuity_without_request_metadata(self) -> None:
        """checks story context enters the prompt without request metadata"""

        request_payload = dict(VALID_REQUEST)
        request_payload["requestId"] = "trace-only-id"
        request_payload["previousStorySummary"] = (
            "The hero stopped the Ashen Order's first ritual."
        )

        user_prompt = build_user_prompt(request_payload)
        system_prompt = build_system_prompt()

        # story context is input data but the tracing id must stay out of the prompt
        self.assertIn("stopped the Ashen Order", user_prompt)
        self.assertNotIn("trace-only-id", user_prompt)
        self.assertNotIn("requestId", user_prompt)
        self.assertIn("rolling summary", system_prompt)
        self.assertIn("Never expose raw gameplay metadata", system_prompt)
        self.assertIn("they are not a checklist", system_prompt)
        self.assertIn("Never enumerate unavailable abilities", system_prompt)
        self.assertIn("in-world prose", system_prompt)
        self.assertIn("Use original wording", system_prompt)

    def test_rejects_empty_tone(self) -> None:
        """checks that the http route rejects a blank writing tone"""

        invalid_request = dict(VALID_REQUEST)
        invalid_request["tone"] = "   "

        request = Request(
            f"http://127.0.0.1:{self.port}/generate-narrative",
            data=json.dumps(invalid_request).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with self.assertRaises(HTTPError) as raised:
            urlopen(request)

        self.assertEqual(raised.exception.code, 400)
        payload = json.load(raised.exception)
        self.assertIn("tone cannot be empty", payload["error"])

    def test_rejects_tone_over_1000_characters(self) -> None:
        """checks that the http route rejects an oversized writing tone"""

        invalid_request = dict(VALID_REQUEST)
        invalid_request["tone"] = "x" * 1001

        request = Request(
            f"http://127.0.0.1:{self.port}/generate-narrative",
            data=json.dumps(invalid_request).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with self.assertRaises(HTTPError) as raised:
            urlopen(request)

        self.assertEqual(raised.exception.code, 400)
        payload = json.load(raised.exception)
        self.assertIn("tone cannot exceed 1000", payload["error"])

    def test_rejects_missing_required_field(self) -> None:
        """checks that the http route reports a missing required field"""

        invalid_request = dict(VALID_REQUEST)
        del invalid_request["scenarioId"]
        request = Request(
            f"http://127.0.0.1:{self.port}/generate-narrative",
            data=json.dumps(invalid_request).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with self.assertRaises(HTTPError) as raised:
            urlopen(request)

        self.assertEqual(raised.exception.code, 400)
        payload = json.load(raised.exception)
        self.assertIn("scenarioId", payload["error"])


if __name__ == "__main__":
    # runs these tests when this file is started directly
    unittest.main()

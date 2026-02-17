#!/usr/bin/env python
"""Interactive manual test runner with user input capture."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


@dataclass
class ManualStep:
    kind: str
    label: str
    command: str | None = None
    command_template: str | None = None


@dataclass
class ManualTest:
    test_id: str
    title: str
    steps: list[ManualStep]


class ManualTestRunner:
    def __init__(self, spec_path: Path, output_dir: Path) -> None:
        self.spec_path = spec_path
        self.output_dir = output_dir

    def load_tests(self) -> list[ManualTest]:
        with self.spec_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        tests_data = payload.get("tests", [])
        tests: list[ManualTest] = []
        for item in tests_data:
            steps = [
                ManualStep(
                    kind=step.get("kind", "user"),
                    label=step.get("label", ""),
                    command=step.get("command"),
                    command_template=step.get("command_template"),
                )
                for step in item.get("steps", [])
            ]
            tests.append(
                ManualTest(
                    test_id=item.get("id", ""),
                    title=item.get("title", ""),
                    steps=steps,
                )
            )
        return tests

    def select_test(self, tests: list[ManualTest], test_id: str | None) -> ManualTest:
        if test_id:
            for test in tests:
                if test.test_id == test_id:
                    return test
            raise ValueError(f"Unknown test id: {test_id}")
        if len(tests) == 1:
            return tests[0]
        print("Available manual tests:")
        for index, test in enumerate(tests, start=1):
            print(f"{index}. {test.test_id} - {test.title}")
        choice = self._prompt_int("Select a test", 1, len(tests))
        return tests[choice - 1]

    def run(self, test: ManualTest) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = self.output_dir / f"{test.test_id}-{timestamp}.md"
        results: list[str] = []
        variables: dict[str, str] = {}  # Store captured variables like expense_key
        print(f"\nRunning manual test: {test.title}")

        setup_step = ManualStep(
            kind="user",
            label="Confirm hb-config.json is configured and connected to WiFi",
            command=None,
        )
        steps = [setup_step, *test.steps]

        for index, step in enumerate(steps, start=1):
            print(f"\n{'='*70}")
            print(f"Step {index}: {step.label}")
            if step.kind == "auto":
                # Execute auto step
                command = step.command
                if step.command_template:
                    command = step.command_template.format(**variables)
                print(f"Command: {command}")
                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    print(f"Output:\n{result.stdout}")
                    if result.returncode != 0:
                        print(f"Error:\n{result.stderr}", file=sys.stderr)
                        status = "fail"
                        notes = f"Command failed: {result.stderr[:200]}"
                    else:
                        status = "pass"
                        notes = ""
                except subprocess.TimeoutExpired:
                    status = "fail"
                    notes = "Command timeout"
                except Exception as e:
                    status = "fail"
                    notes = str(e)
                results.append(self._format_result(index, step, status, notes, command))
            else:
                # User verification step
                print("This step requires your manual verification.")
                status = self._prompt_choice("Result", ["pass", "fail", "skip"])
                if status == "pass" and "Record" in step.label and "key" in step.label.lower():
                    # Prompt for variable input if this is a recording step
                    key_input = input("Enter the value: ").strip()
                    if key_input:
                        variables["expense_key"] = key_input
                        print(f"Recorded: expense_key = {key_input}")
                notes = input("Notes (optional): ").strip()
                results.append(self._format_result(index, step, status, notes))

        overall = self._prompt_choice("Overall result", ["pass", "fail", "incomplete"])
        overall_notes = input("Overall notes (optional): ").strip()
        self._write_report(output_path, test, results, overall, overall_notes)
        print(f"\nWrote results to {output_path}")
        return output_path

    def _write_report(
        self,
        output_path: Path,
        test: ManualTest,
        results: list[str],
        overall: str,
        overall_notes: str,
    ) -> None:
        lines = [
            "# Manual test result",
            "",
            "## Table of contents",
            "",
            "- [Summary](#summary)",
            "- [Step results](#step-results)",
            "",
            "## Summary",
            "",
            f"Test id: {test.test_id}",
            f"Title: {test.title}",
            f"Timestamp: {datetime.now().isoformat(timespec='seconds')}",
            f"Overall result: {overall}",
            f"Overall notes: {overall_notes}",
            "",
            "## Step results",
            "",
        ]
        lines.extend(results)
        content = "\n".join(lines) + "\n"
        with output_path.open("w", encoding="utf-8") as handle:
            handle.write(content)

    @staticmethod
    def _format_result(
        index: int, step: ManualStep, status: str, notes: str, command: str | None = None
    ) -> str:
        if command:
            command_line = f"Command: {command}"
        elif step.command:
            command_line = f"Command: {step.command}"
        else:
            command_line = "Command: none"
        return "\n".join(
            [
                f"### Step {index}",
                f"Kind: {step.kind}",
                f"Label: {step.label}",
                command_line,
                f"Status: {status}",
                f"Notes: {notes}",
                "",
            ]
        )

    @staticmethod
    def _prompt_choice(prompt: str, options: list[str]) -> str:
        option_text = "/".join(options)
        while True:
            value = input(f"\n{prompt} [{option_text}]: ").strip().lower()
            if value in options:
                return value
            print(f"Choose one of: {', '.join(options)}")

    @staticmethod
    def _prompt_int(prompt: str, min_value: int, max_value: int) -> int:
        while True:
            raw = input(f"\n{prompt} [{min_value}-{max_value}]: ").strip()
            if raw.isdigit():
                value = int(raw)
                if min_value <= value <= max_value:
                    return value
            print(f"Enter a number between {min_value} and {max_value}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run manual test procedures.")
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path("tests/manual/manual_tests.json"),
        help="Path to manual test spec JSON.",
    )
    parser.add_argument(
        "--test-id",
        type=str,
        help="Run a specific test id from the spec.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available tests and exit.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tests/manual/results"),
        help="Directory for result reports.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runner = ManualTestRunner(args.spec, args.output_dir)
    tests = runner.load_tests()
    if not tests:
        raise ValueError("No tests found in the spec file.")
    
    if args.list:
        print("Available tests:")
        for test in tests:
            print(f"  {test.test_id}: {test.title}")
        return
    
    selected = runner.select_test(tests, args.test_id)
    try:
        runner.run(selected)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()

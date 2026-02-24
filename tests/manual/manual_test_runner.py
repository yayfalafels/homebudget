#!/usr/bin/env python
"""Interactive manual test runner with user input capture."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


@dataclass
class InputField:
    name: str
    label: str
    type: str = "string"


@dataclass
class ManualStep:
    kind: str
    label: str
    command: str | None = None
    command_template: str | None = None
    template: str | None = None
    template_command: str | None = None
    input_fields: list[InputField] | None = None


@dataclass
class ManualTest:
    test_id: str
    title: str
    steps: list[ManualStep]
    resource: str | None = None


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
            steps = []
            for step in item.get("steps", []):
                # Parse input_fields if present
                input_fields = None
                if "input_fields" in step:
                    input_fields = [
                        InputField(
                            name=field.get("name", ""),
                            label=field.get("label", ""),
                            type=field.get("type", "string"),
                        )
                        for field in step.get("input_fields", [])
                    ]
                
                steps.append(
                    ManualStep(
                        kind=step.get("kind", "user"),
                        label=step.get("label", ""),
                        command=step.get("command"),
                        command_template=step.get("command_template"),
                        template=step.get("template"),
                        template_command=step.get("template_command"),
                        input_fields=input_fields,
                    )
                )
            tests.append(
                ManualTest(
                    test_id=item.get("id", ""),
                    title=item.get("title", ""),
                    steps=steps,
                    resource=item.get("resource"),
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

    def _extract_error_message(self, stderr: str) -> str:
        """Extract the meaningful error message from stderr output.
        
        Handles Click ClickException output format which typically ends with:
        Error: <message>
        """
        lines = stderr.strip().split('\n')
        # Look for ClickException messages (lines starting with "Error:")
        for line in reversed(lines):
            if line.startswith('Error:'):
                return line[7:].strip()  # Remove "Error: " prefix
            if 'NotFoundError' in line:
                # Extract meaningful error from exception message
                if ':' in line:
                    return line.split(':', 1)[1].strip()
        # Fall back to last non-empty line
        return lines[-1] if lines else "Unknown error"

    def _load_batch_operations(self, batch_file: str, variables: dict[str, str]) -> str:
        """Load batch template JSON and substitute variable placeholders.
        
        Supports expansion of {TRANSFER_KEYS} into multiple delete operations.
        When {TRANSFER_KEYS} contains comma-separated values, creates individual
        delete operations for each key.
        
        Args:
            batch_file: Path to batch template JSON file (can be relative to tests/manual/
                       or fully qualified from workspace root)
            variables: Dict of variables to substitute (e.g., {EXPENSE_KEY} -> value)
            
        Returns:
            Path to temporary JSON file with substituted variables
        """
        # Handle both formats: "batch_templates/..." and "tests/manual/batch_templates/..."
        if batch_file.startswith("tests/manual/"):
            batch_path = Path(batch_file)
        else:
            batch_path = Path("tests/manual") / batch_file
        
        if not batch_path.exists():
            raise ValueError(f"Batch template file not found: {batch_path}")
        
        # Load original operations from template
        with batch_path.open("r", encoding="utf-8") as handle:
            operations = json.load(handle)
        
        # Handle TRANSFER_KEYS expansion: split comma-separated values into multiple delete operations
        transfer_keys = variables.get("transfer_keys", "")
        if transfer_keys:
            # Parse comma-separated transfer keys
            keys_list = [k.strip() for k in transfer_keys.split(",") if k.strip()]
            
            # Expand operations: for each transfer delete operation with {TRANSFER_KEYS},
            # create one operation per key
            expanded_operations = []
            for op in operations:
                if (op.get("resource") == "transfer" and 
                    op.get("operation") == "delete" and
                    op.get("parameters", {}).get("key") == "{TRANSFER_KEYS}"):
                    # Create individual delete operations for each key
                    for key in keys_list:
                        expanded_operations.append({
                            "resource": "transfer",
                            "operation": "delete",
                            "parameters": {"key": key}
                        })
                else:
                    expanded_operations.append(op)
            operations = expanded_operations
        
        # Substitute other variables in all parameter values
        operations_str = json.dumps(operations)
        for var_name, var_value in variables.items():
            if var_name == "transfer_keys":
                # Transfer keys were already expanded above
                continue
            placeholder = f"{{{var_name.upper()}}}"
            operations_str = operations_str.replace(placeholder, str(var_value))
        
        # Write substituted operations to temporary file
        temp_path = self.output_dir / f"batch_temp_{len(variables)}.json"
        with temp_path.open("w", encoding="utf-8") as handle:
            handle.write(operations_str)
        
        return str(temp_path)

    def _extract_keys_from_batch_output(self, output: str) -> dict[str, str]:
        """Extract record keys from batch operation output.
        
        Batch operations return JSON with successful records containing their keys.
        Example: {"successful": [{"key": 123, ...}, ...]}
        
        Returns:
            Dict mapping key_type (expense_key, income_key, transfer_key) to value
        """
        keys: dict[str, str] = {}
        try:
            # Try to parse as JSON
            result = json.loads(output)
            if not isinstance(result, dict):
                return keys
            
            successful = result.get("successful", [])
            if not successful:
                return keys
            
            # Determine key types from resource field if available
            for record in successful:
                if isinstance(record, dict) and "key" in record:
                    resource = record.get("resource", "")
                    key_value = str(record["key"])
                    
                    if resource == "expense":
                        keys["expense_key"] = key_value
                    elif resource == "income":
                        keys["income_key"] = key_value
                    elif resource == "transfer":
                        keys["transfer_key"] = key_value
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass
        
        return keys

    def _extract_balance_from_output(self, output: str) -> dict[str, str]:
        """Extract balance information from balance query CLI output.
        
        The balance command outputs formatted text like:
            Account Balance: TWH IB USD
            Query Date: 2025-11-30
            Balance: 1502.89
            
            Reconcile Date: 2025-11-30
            Reconcile Amount: 1502.89
        
        Returns:
            Dict with extracted balance data (cli_balance key)
        """
        balance_data: dict[str, str] = {}
        try:
            # Look for "Balance: <amount>" line
            match = re.search(r'^Balance:\s*([-\d.]+)', output, re.MULTILINE)
            if match:
                balance_amount = match.group(1)
                balance_data["cli_balance"] = balance_amount
        except Exception:
            pass
        
        return balance_data

    def _find_matching_ui_balance_key(self, variables: dict[str, str], step_label: str) -> str | None:
        """Find the UI balance variable key that matches the current step.
        
        For steps like "[Test 1] Query CLI balance for Account 1", looks for ui_balance_1.
        For simple steps without numbers, looks for ui_balance.
        
        Args:
            variables: Dict of all captured variables
            step_label: The label of the current step
            
        Returns:
            The variable key (e.g., 'ui_balance_1') or None if not found
        """
        # Check if step label contains a test number like "[Test 1]"
        test_match = re.search(r'\[Test (\d+)\]', step_label)
        if test_match:
            test_num = test_match.group(1)
            ui_balance_key = f"ui_balance_{test_num}"
            if ui_balance_key in variables:
                return ui_balance_key
        
        # Check for boundary case variables: ui_balance_old, ui_balance_recent, ui_balance_today
        if "[Old date]" in step_label:
            return "balance_old" if "balance_old" in variables else None
        elif "[Recent date]" in step_label:
            return "balance_recent" if "balance_recent" in variables else None
        elif "[Today]" in step_label:
            return "balance_today" if "balance_today" in variables else None
        
        # Default: look for simple ui_balance
        if "ui_balance" in variables:
            return "ui_balance"
        
        return None

    def _compare_balances(self, ui_balance_str: str, cli_balance_str: str, balance_key: str) -> str:
        """Compare UI balance with CLI balance and return comparison result.
        
        Args:
            ui_balance_str: Balance value from UI (as string)
            cli_balance_str: Balance value from CLI (as string)
            balance_key: The variable key name (for reporting)
            
        Returns:
            String with comparison result, marked with ✓ for match or ✗ for mismatch
        """
        try:
            from decimal import Decimal
            ui_val = Decimal(str(ui_balance_str).strip())
            cli_val = Decimal(str(cli_balance_str).strip())
            if ui_val == cli_val:
                return f"✓ Balance match ({balance_key}): {ui_balance_str} == {cli_balance_str}"
            else:
                diff = abs(ui_val - cli_val)
                return f"✗ Balance mismatch ({balance_key}): {ui_balance_str} != {cli_balance_str} (diff: {diff})"
        except Exception as e:
            return f"✗ Unable to compare balances: {str(e)}"

    def _process_batch_command(self, command: str, variables: dict[str, str]) -> str:
        """Process a command that references a batch template file.
        
        Only processes template files that contain variable placeholders ({VARIABLE_NAME}).
        For files without placeholders, returns the command unchanged.
        """
        # Check if command has --file with batch_templates path
        match = re.search(r'--file\s+((?:tests/manual/)?batch_templates/\S+\.json)', command)
        if not match:
            return command
        
        batch_file_relative = match.group(1)
        
        # Handle both formats: "batch_templates/..." and "tests/manual/batch_templates/..."
        if batch_file_relative.startswith("tests/manual/"):
            batch_path = Path(batch_file_relative)
        else:
            batch_path = Path("tests/manual") / batch_file_relative
        
        if not batch_path.exists():
            return command
        
        # Check if file contains placeholders before processing
        try:
            with batch_path.open("r", encoding="utf-8") as handle:
                content = handle.read()
            # Look for placeholder pattern {WORD} or transfer_keys expansion needed
            has_placeholder = bool(re.search(r'\{[A-Z_]+\}', content))
            needs_transfer_expansion = "transfer_keys" in variables
            
            if not has_placeholder and not needs_transfer_expansion:
                return command
        except (OSError, UnicodeDecodeError):
            return command
        
        # Load and substitute variables
        batch_json = self._load_batch_operations(batch_file_relative, variables)
        
        # Replace the original batch template file path with temp file path
        new_command = command.replace(batch_file_relative, batch_json)
        return new_command

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
                command = None
                
                # Determine the command to run
                if step.command:
                    command = step.command
                elif step.command_template:
                    # Check if this is a rollback step and all key variables are empty - skip if so
                    if "rollback" in step.label.lower():
                        key_vars = ["transfer_keys", "expense_keys", "income_keys"]
                        has_keys = any(variables.get(key, "").strip() for key in key_vars)
                        if not has_keys:
                            print("Skipped: No keys recorded (no items to rollback)")
                            continue
                    command = step.command_template.format(**variables)
                
                if not command:
                    print("Warning: auto step has no command or command_template", file=sys.stderr)
                    continue
                
                # Process template if specified - expands variables and writes temp file
                if step.template:
                    temp_json = self._load_batch_operations(step.template, variables)
                    # Use template_command as the base (e.g., "hb batch run --file")
                    # and append the temp file path
                    if step.template_command:
                        command = f"{step.template_command} {temp_json}"
                    else:
                        # Fallback: extract base command from original command
                        match = re.search(r'hb batch run --file', command)
                        if match:
                            command = f"hb batch run --file {temp_json}"
                
                # Process batch commands (substitute {PLACEHOLDER} and handle --file)
                command = self._process_batch_command(command, variables)
                
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
                        error_msg = self._extract_error_message(result.stderr)
                        print(f"Error: {error_msg}", file=sys.stderr)
                        status = "fail"
                        notes = f"Command failed: {error_msg[:200]}"
                    else:
                        status = "pass"
                        notes = ""
                        # Extract keys from batch output for next operations
                        new_keys = self._extract_keys_from_batch_output(result.stdout)
                        variables.update(new_keys)
                        if new_keys:
                            notes = f"Keys recorded: {', '.join(new_keys.keys())}"
                        
                        # Extract balance from balance query output and auto-compare with UI balance
                        if "balance" in command.lower() and "account balance" in command.lower():
                            balance_data = self._extract_balance_from_output(result.stdout)
                            if balance_data:
                                variables.update(balance_data)
                                cli_balance_str = balance_data.get('cli_balance', '')
                                
                                # Find matching UI balance variable(s)
                                # Look for ui_balance, ui_balance_1, ui_balance_2, etc.
                                ui_balance_key = self._find_matching_ui_balance_key(variables, step.label)
                                if ui_balance_key:
                                    ui_balance_str = variables.get(ui_balance_key, '')
                                    notes = self._compare_balances(ui_balance_str, cli_balance_str, ui_balance_key)
                                    # Set status based on comparison
                                    if "✓" in notes:
                                        status = "pass"
                                    elif "✗" in notes:
                                        status = "fail"
                                else:
                                    notes = f"CLI Balance: {cli_balance_str}"
                    
                    # After showing output, allow user to rerun list commands with different limit
                    if status == "pass" and "list" in command and "--limit" in command:
                        modify = input(f"\nRun again with different limit? [y/N]: ").strip().lower()
                        if modify == "y":
                            new_limit = input("Enter new limit (e.g., 10, 20): ").strip()
                            if new_limit.isdigit():
                                # Replace the limit value in the command
                                new_command = re.sub(r'--limit\s+\d+', f'--limit {new_limit}', command)
                                print(f"\nCommand: {new_command}")
                                result = subprocess.run(
                                    new_command,
                                    shell=True,
                                    capture_output=True,
                                    text=True,
                                    timeout=30,
                                )
                                print(f"Output:\n{result.stdout}")
                                if result.returncode != 0:
                                    error_msg = self._extract_error_message(result.stderr)
                                    print(f"Error: {error_msg}", file=sys.stderr)
                                else:
                                    command = new_command  # Update command for results
                
                except subprocess.TimeoutExpired:
                    status = "fail"
                    notes = "Command timeout"
                except Exception as e:
                    status = "fail"
                    notes = str(e)
                results.append(self._format_result(index, step, status, notes, command))
            else:
                # User step - may have input_fields to capture or require verification
                status = "pass"
                notes = ""
                
                # If step has input_fields, prompt for them
                if step.input_fields:
                    print("\nPlease provide the following information:")
                    for field in step.input_fields:
                        user_input = input(f"  {field.label}: ").strip()
                        if user_input:
                            variables[field.name] = user_input
                
                # For verification steps (without input_fields), ask for pass/fail
                if not step.input_fields:
                    print("\nThis step requires your manual verification.")
                    status = self._prompt_choice("Result", ["pass", "fail", "skip"])
                    
                    # If this is a verification step with potential balance comparison, extract and compare
                    if "verify" in step.label.lower() and "balance" in step.label.lower():
                        ui_balance = variables.get("ui_balance")
                        cli_balance = variables.get("cli_balance")
                        
                        if ui_balance and cli_balance:
                            print(f"\nBalance comparison:")
                            print(f"  UI balance:  {ui_balance}")
                            print(f"  CLI balance: {cli_balance}")
                            
                            try:
                                from decimal import Decimal
                                ui_val = Decimal(str(ui_balance))
                                cli_val = Decimal(str(cli_balance))
                                if ui_val == cli_val:
                                    notes = f"✓ Match: {ui_balance} == {cli_balance}"
                                else:
                                    diff = abs(ui_val - cli_val)
                                    notes = f"✗ Differ by {diff}: {ui_balance} != {cli_balance}"
                            except Exception:
                                notes = f"UI={ui_balance}, CLI={cli_balance}"
                
                results.append(self._format_result(index, step, status, notes))
        
        # Compute overall result
        overall = "pass"
        for result in results:
            if "Status: fail" in result:
                overall = "fail"
                break
        
        # Write report
        self._write_report(output_path, test, results, overall, "")
        
        # Print summary to console
        print(f"\n{'='*70}")
        print(f"TEST RESULT: {overall.upper()}")
        print(f"{'='*70}")
        
        # Extract and print key findings (balance comparisons, etc.)
        for result in results:
            if "Balance match" in result or "Balance mismatch" in result:
                # Extract the notes line from the result
                match = re.search(r'Notes: (.+?)(?:\n|$)', result)
                if match:
                    notes = match.group(1)
                    print(f"  {notes}")
        
        print(f"\nReport written to: {output_path}\n")
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

    @staticmethod
    def _determine_key_type(label: str, resource: str) -> str:
        """Determine the key variable name based on resource type or label."""
        # Check resource first
        if resource == "expense":
            return "expense_key"
        elif resource == "income":
            return "income_key"
        elif resource == "transfer":
            return "transfer_key"
        # Fallback: check label
        label_lower = label.lower()
        if "expense" in label_lower:
            return "expense_key"
        elif "income" in label_lower:
            return "income_key"
        elif "transfer" in label_lower:
            return "transfer_key"
        # Default fallback
        return "key"


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

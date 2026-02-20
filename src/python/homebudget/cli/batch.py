"""Batch CLI commands for mixed resource operations."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from decimal import Decimal
import json
from pathlib import Path

import click

from homebudget.cli.common import get_client
from homebudget.models import BatchOperation


def _serialize_batch_result(result):
    """Convert BatchOperationResult to JSON-serializable dict.
    
    Handles Decimal -> str conversion and date -> isoformat() for JSON compatibility.
    """
    def serialize_value(v):
        if isinstance(v, Decimal):
            return str(v)
        if isinstance(v, date):
            return v.isoformat()
        if hasattr(v, '__dataclass_fields__'):
            return {k: serialize_value(getattr(v, k)) for k in v.__dataclass_fields__}
        if isinstance(v, (list, tuple)):
            return [serialize_value(item) for item in v]
        if isinstance(v, dict):
            return {k: serialize_value(val) for k, val in v.items()}
        return v
    
    return {
        "successful": [serialize_value(asdict(record)) for record in result.successful],
        "failed": [
            {
                "operation": serialize_value(asdict(op)),
                "error": str(exc)
            }
            for op, exc in result.failed
        ]
    }


@click.group(
    help="""Batch operations for mixed resource workflows.

Execute multiple operations (add, update, delete) across different resources
(expense, income, transfer) in a single atomic batch transaction.

USAGE:
  hb batch run --file <path-to-json>

EXAMPLES:
  Run batch operations from a JSON file:
    hb batch run --file operations.json
  
  Run batch and stop on first error:
    hb batch run --file operations.json --stop-on-error
  
  Run batch and save errors to a report:
    hb batch run --file operations.json --error-report errors.json

JSON FILE FORMAT:
  Array of operation objects, each with:
  - resource: "expense", "income", or "transfer"
  - operation: "add", "update", or "delete"
  - key: (optional, required for update/delete)
  - params: object with operation parameters

EXAMPLE JSON:
  [
    {
      "resource": "expense",
      "operation": "add",
      "params": {
        "date": "2026-02-20",
        "category": "Food (Basic)",
        "subcategory": "Restaurant",
        "amount": 25.50,
        "account": "TWH - Personal"
      }
    },
    {
      "resource": "expense",
      "operation": "update",
      "key": 12345,
      "params": {
        "notes": "Updated notes"
      }
    },
    {
      "resource": "transfer",
      "operation": "add",
      "params": {
        "date": "2026-02-20",
        "from_account": "TWH - Personal",
        "to_account": "30 CC Hashemis",
        "amount": 100.00
      }
    }
  ]
""",
)
def batch() -> None:
    """Batch operations for mixed resource workflows."""


@batch.command("run")
@click.option(
    "--file",
    "file_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to JSON file containing batch operations.",
)
@click.option(
    "--stop-on-error",
    is_flag=True,
    help="Stop processing on first error. Default is to continue and report errors.",
)
@click.option(
    "--error-report",
    type=click.Path(path_type=Path),
    help="Write error details to this file.",
)
@click.pass_context
def run(
    ctx: click.Context,
    file_path: Path,
    stop_on_error: bool,
    error_report: Path | None,
) -> None:
    """Run a batch of mixed resource operations from a JSON file."""
    errors: list[str] = []
    operations: list[BatchOperation] = []

    try:
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, list):
            raise click.ClickException("Batch JSON must be an array of operations")

        # Parse operations
        for index, op in enumerate(payload):
            try:
                operations.append(
                    BatchOperation(
                        resource=op.get("resource"),
                        operation=op.get("operation"),
                        parameters=op.get("parameters", {}),
                    )
                )
            except (KeyError, TypeError) as e:
                msg = f"Operation {index}: Invalid operation format - {e}"
                errors.append(msg)
                if stop_on_error:
                    raise click.ClickException(msg)

        if not operations:
            raise click.ClickException("No valid operations found in batch file")

        # Execute batch with repository connection
        client = get_client(ctx)
        with client:
            result = client.batch(operations, continue_on_error=not stop_on_error)

    except (json.JSONDecodeError, OSError) as e:
        raise click.ClickException(f"Error reading batch file: {e}")

    click.echo("\nBatch operations completed")
    click.echo(json.dumps(_serialize_batch_result(result), indent=2))

    if error_report and errors:
        with error_report.open("w", encoding="utf-8") as handle:
            json.dump(errors, handle, indent=2)
        click.echo(f"\nErrors written to {error_report}")

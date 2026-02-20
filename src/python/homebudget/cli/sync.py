"""Sync CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import click

from homebudget.cli.common import get_client
from homebudget.models import BatchOperation


@click.group()
def sync() -> None:
    """Sync commands."""


@sync.command("batch")
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
def batch(
    ctx: click.Context,
    file_path: Path,
    stop_on_error: bool,
    error_report: Path | None,
) -> None:
    """Run a mixed batch of sync operations from a JSON file."""
    errors: list[str] = []
    operations: list[BatchOperation] = []

    try:
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:
        raise click.ClickException(f"Failed to read JSON file: {exc}") from exc

    if not isinstance(payload, list):
        raise click.ClickException("Batch JSON must be an array of operations")

    for index, item in enumerate(payload, start=1):
        try:
            if not isinstance(item, dict):
                raise ValueError("Operation must be a JSON object")
            resource = item.get("resource")
            operation = item.get("operation")
            parameters = item.get("parameters")
            if not resource or not operation or parameters is None:
                raise ValueError("Operation requires resource, operation, and parameters")
            if not isinstance(parameters, dict):
                raise ValueError("Operation parameters must be an object")
            operations.append(
                BatchOperation(
                    resource=str(resource),
                    operation=str(operation),
                    parameters=parameters,
                )
            )
        except Exception as exc:
            errors.append(f"Item {index}: {exc}")
            if stop_on_error:
                raise click.ClickException(f"Error at item {index}: {exc}") from exc

    if not operations and errors:
        click.echo(f"Failed to parse any operations. {len(errors)} errors.")
        if error_report:
            error_report.write_text("\n".join(errors), encoding="utf-8")
            click.echo(f"Error details written to {error_report}")
        return

    with get_client(ctx) as client:
        result = client.batch(operations, continue_on_error=not stop_on_error)

    click.echo("\nBatch sync completed")
    click.echo(f"  Successful: {len(result.successful)}")
    click.echo(f"  Failed: {len(result.failed)}")

    if result.failed:
        click.echo("\nFailed operations:")
        for failed_operation, exception in result.failed:
            click.echo(
                f"  {failed_operation.resource} {failed_operation.operation}: {exception}"
            )

    if error_report and (errors or result.failed):
        all_errors = errors[:]
        for failed_operation, exception in result.failed:
            all_errors.append(
                f"Failed operation: {failed_operation.resource} "
                f"{failed_operation.operation} - {exception}"
            )
        error_report.write_text("\n".join(all_errors), encoding="utf-8")
        click.echo(f"\nError details written to {error_report}")

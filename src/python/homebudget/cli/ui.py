"""UI control CLI commands."""

from __future__ import annotations

import click

from homebudget.ui_control import HomeBudgetUIController


@click.group()
def ui() -> None:
    """UI control commands."""


@ui.command("start")
@click.option("--no-verify", is_flag=True, help="Skip verification of UI state.")
@click.option("--verify-attempts", type=int, default=5, help="Max verification attempts.")
@click.option("--verify-delay", type=float, default=0.5, help="Delay between verification attempts (seconds).")
@click.option("--settle-time", type=float, default=2.0, help="Time to allow UI to fully initialize (seconds).")
def start_ui(
    no_verify: bool,
    verify_attempts: int,
    verify_delay: float,
    settle_time: float,
) -> None:
    """Start the HomeBudget UI."""
    verify = not no_verify
    success, message = HomeBudgetUIController.open(
        verify=verify,
        verify_attempts=verify_attempts,
        verify_delay=verify_delay,
        settle_time=settle_time,
    )
    if success:
        click.echo(f"✓ UI started successfully: {message}")
    else:
        click.echo(f"✗ UI start failed: {message}", err=True)
        raise click.Abort()


@ui.command("close")
@click.option("--no-verify", is_flag=True, help="Skip verification of UI state.")
@click.option("--verify-attempts", type=int, default=5, help="Max verification attempts.")
@click.option("--verify-delay", type=float, default=0.3, help="Delay between verification attempts (seconds).")
@click.option("--no-force", is_flag=True, help="Don't force kill the UI process.")
def close_ui(
    no_verify: bool,
    verify_attempts: int,
    verify_delay: float,
    no_force: bool,
) -> None:
    """Close the HomeBudget UI."""
    verify = not no_verify
    force_kill = not no_force
    success, message = HomeBudgetUIController.close(
        verify=verify,
        verify_attempts=verify_attempts,
        verify_delay=verify_delay,
        force_kill=force_kill,
    )
    if success:
        click.echo(f"✓ UI closed successfully: {message}")
    else:
        click.echo(f"✗ UI close failed: {message}", err=True)
        raise click.Abort()


@ui.command("refresh")
@click.option("--no-verify", is_flag=True, help="Skip verification of UI state.")
@click.option("--close-verify-attempts", type=int, default=5, help="Max close verification attempts.")
@click.option("--close-verify-delay", type=float, default=0.3, help="Delay between close verification attempts (seconds).")
@click.option("--open-verify-attempts", type=int, default=5, help="Max open verification attempts.")
@click.option("--open-verify-delay", type=float, default=0.5, help="Delay between open verification attempts (seconds).")
@click.option("--settle-time", type=float, default=2.0, help="Time to allow UI to fully initialize (seconds).")
@click.option("--no-force", is_flag=True, help="Don't force kill the UI process.")
def refresh_ui(
    no_verify: bool,
    close_verify_attempts: int,
    close_verify_delay: float,
    open_verify_attempts: int,
    open_verify_delay: float,
    settle_time: float,
    no_force: bool,
) -> None:
    """Refresh the HomeBudget UI (close and reopen)."""
    verify = not no_verify
    force_kill = not no_force
    
    # Close UI
    click.echo("Closing UI...")
    close_success, close_message = HomeBudgetUIController.close(
        verify=verify,
        verify_attempts=close_verify_attempts,
        verify_delay=close_verify_delay,
        force_kill=force_kill,
    )
    
    if not close_success:
        click.echo(f"✗ UI close failed: {close_message}", err=True)
        raise click.Abort()
    
    click.echo(f"✓ UI closed: {close_message}")
    
    # Open UI
    click.echo("Opening UI...")
    open_success, open_message = HomeBudgetUIController.open(
        verify=verify,
        verify_attempts=open_verify_attempts,
        verify_delay=open_verify_delay,
        settle_time=settle_time,
    )
    
    if not open_success:
        click.echo(f"✗ UI open failed: {open_message}", err=True)
        raise click.Abort()
    
    click.echo(f"✓ UI refreshed successfully: {open_message}")


@ui.command("status")
def status_ui() -> None:
    """Check the current status of the HomeBudget UI."""
    status = HomeBudgetUIController.get_status()
    if status == "open":
        click.echo("✓ HomeBudget UI is OPEN")
    elif status == "closed":
        click.echo("○ HomeBudget UI is CLOSED")
    else:
        click.echo(f"? HomeBudget UI status: {status}")

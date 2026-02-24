"""Category CLI commands."""

from __future__ import annotations

import click

from homebudget.cli.common import get_client
from homebudget.exceptions import NotFoundError


@click.group()
def category() -> None:
    """Category commands."""


@category.command("list")
@click.pass_context
def list_categories(ctx: click.Context) -> None:
    """List all expense categories ordered by sequence number.
    
    Displays categories that can be used for categorizing expenses.
    
    Examples:
        hb category list
    """
    with get_client(ctx) as client:
        categories = client.get_categories()
        
        if not categories:
            click.echo("No categories found.")
            return
        
        # Format as table
        click.echo("\nCategories:")
        click.echo("-" * 60)
        click.echo(f"{'Seq':<5} {'Name':<50}")
        click.echo("-" * 60)
        
        for category in categories:
            click.echo(f"{category.seqNum:<5} {category.name:<50}")
        
        click.echo("-" * 60)


@category.command("subcategories")
@click.option("--category", required=True, help="Parent category name.")
@click.pass_context
def list_subcategories(ctx: click.Context, category: str) -> None:
    """List subcategories for a category.
    
    Displays all subcategories under the given parent category,
    ordered by sequence number.
    
    Examples:
        hb category subcategories --category "Groceries"
        hb category subcategories --category "Utilities"
    """
    with get_client(ctx) as client:
        try:
            subcategories = client.get_subcategories(category)
        except NotFoundError as e:
            raise click.ClickException(str(e))
        
        if not subcategories:
            click.echo(f"No subcategories found for category '{category}'.")
            return
        
        # Format as table
        click.echo(f"\nSubcategories for '{category}':")
        click.echo("-" * 60)
        click.echo(f"{'Seq':<5} {'Name':<50}")
        click.echo("-" * 60)
        
        for subcat in subcategories:
            click.echo(f"{subcat.seqNum:<5} {subcat.name:<50}")
        
        click.echo("-" * 60)

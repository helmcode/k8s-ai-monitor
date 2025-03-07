from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown


console = Console()


def show_info():
    info_text = """
    # Kubernetes Monitor CLI

    This tool allows you to monitor your Kubernetes clusters
    and get recommendations based on the analysis of detected issues.

    ## Available Commands

    * `info` - Show this information about the tool

    ## Upcoming Features

    * Cluster monitoring
    * Issue detection
    * AI-powered recommendations
    * Results export
    """

    console.print(Panel(
        Markdown(info_text),
        title="Kubernetes Monitor - Info",
        border_style="green",
        padding=(1, 2),
    ))

    console.print("\n[bold]Usage Examples:[/bold]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Command")
    table.add_column("Description")

    table.add_row(
        "kai info",
        "Show detailed information about the tool"
    )
    console.print(table)

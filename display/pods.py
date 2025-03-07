from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


console = Console()


def display_issue(issue: Dict[str, Any], analysis: Dict[str, str]):
    """
    Display an issue with its analysis in a rich format

    Args:
        issue: The issue details
        analysis: The AI analysis with diagnosis and recommendations
    """
    severity = issue.get("severity", "Medium")
    severity_color = "red" if severity == "High" else "yellow" if severity == "Medium" else "blue"

    # Create the main panel
    console.print()
    console.print(Panel(
        f"[bold {severity_color}]{issue['issue_type']}[/bold {severity_color}]: {issue['resource_name']}",
        title=f"[{severity_color}]Issue Detected in {issue['namespace']}[/{severity_color}]",
        border_style=severity_color
    ))

    # Display issue details
    console.print(f"[bold]Description:[/bold] {issue['description']}")
    console.print(f"[bold]Detected at:[/bold] {issue['detected_at']}")
    console.print()

    # Display AI analysis
    console.print(Panel(
        f"[bold]Diagnosis:[/bold]\n{analysis['diagnosis']}\n\n[bold]Recommendations:[/bold]\n{analysis['recommendations']}",
        title="AI Analysis",
        border_style="green"
    ))

    # Display logs excerpt
    if "logs" in issue and issue["logs"]:
        logs = issue["logs"]
        if isinstance(logs, str):
            # Take only the last few lines to avoid overwhelming output
            log_lines = logs.strip().split("\n")
            if len(log_lines) > 10:
                log_excerpt = "\n".join(log_lines[-10:])
                console.print(Panel(
                    f"{log_excerpt}",
                    title="Recent Logs (last 10 lines)",
                    border_style="blue"
                ))
            else:
                console.print(Panel(
                    f"{logs}",
                    title="Recent Logs",
                    border_style="blue"
                ))

    # Display recent events
    if "events" in issue and issue["events"]:
        events = issue["events"]
        if events:
            table = Table(title="Recent Events")
            table.add_column("Type", style="cyan")
            table.add_column("Reason", style="green")
            table.add_column("Message")
            table.add_column("Count", justify="right")

            # Add the most recent events (up to 5)
            for event in events[:5]:
                table.add_row(
                    event.get("type", ""),
                    event.get("reason", ""),
                    event.get("message", ""),
                    str(event.get("count", 1))
                )

            console.print(table)

    console.print("\n" + "="*80 + "\n")

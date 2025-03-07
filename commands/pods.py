import os
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from monitor.pods import PodMonitor
from display.pods import display_issue

# Import Claude analyzer if API key is available
claudeAnalyzer = None
if os.environ.get("ANTHROPIC_API_KEY"):
    try:
        from ai.claude import ClaudeAnalyzer
        claudeAnalyzer = ClaudeAnalyzer()
    except (ImportError, Exception) as e:
        print(f"Warning: Could not initialize Claude analyzer: {str(e)}")

console = Console()


def monitor_pods(kubeconfig: str, namespaces: List[str]):
    """
    Monitor Kubernetes pods in the specified namespaces

    Args:
        kubeconfig: Path to the kubeconfig file
        namespaces: List of namespaces to monitor
    """
    try:
        # Initialize the Pod monitor
        pod_monitor = PodMonitor(kubeconfig)

        # Display header
        console.print(Panel(
            "[bold]Starting Kubernetes Pod Monitoring[/bold]",
            border_style="green"
        ))

        # Check each namespace
        total_issues = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Scanning namespaces...", total=len(namespaces))

            for namespace in namespaces:
                progress.update(task, description=f"[cyan]Scanning namespace: {namespace}[/cyan]")
                issues = pod_monitor.check_pod_health(namespace)
                total_issues += len(issues)

                for issue in issues:
                    # Use Claude analyzer for analysis
                    if claudeAnalyzer:
                        try:
                            analysis = claudeAnalyzer.analyze_issue_sync(issue)
                        except Exception as e:
                            console.print(f"[bold red]Error using Claude analyzer: {str(e)}[/bold red]")
                            analysis = {
                                "diagnosis": "Error al analizar con Claude AI",
                                "recommendations": "Se requiere una conexión activa con Claude AI para analizar este problema."
                            }
                    else:
                        console.print("[bold yellow]Se requiere la API key de Claude para realizar el análisis.[/bold yellow]")
                        analysis = {
                            "diagnosis": "No se pudo realizar el análisis",
                            "recommendations": "Configure la variable de entorno ANTHROPIC_API_KEY para habilitar el análisis con Claude AI."
                        }

                    display_issue(issue, analysis)

                progress.advance(task)

        # Display summary
        if total_issues == 0:
            console.print(Panel(
                "[bold green]No issues detected in the monitored namespaces.[/bold green]",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[bold yellow]Found {total_issues} issue(s) in the monitored namespaces.[/bold yellow]",
                border_style="yellow"
            ))

    except Exception as e:
        console.print(f"[bold red]Error monitoring pods: {str(e)}[/bold red]")

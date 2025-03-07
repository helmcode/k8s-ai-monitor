import os
import typer
from typing import Optional, Callable, Any
from rich.console import Console


console = Console()


def validate_kubeconfig(value: str) -> str:
    """Validate the kubeconfig file path."""
    if not os.path.exists(value):
        console.print(f"[bold yellow]Warning:[/bold yellow] Kubeconfig file not found: {value}")
        return value

    if not os.path.isfile(value):
        console.print(f"[bold yellow]Warning:[/bold yellow] Kubeconfig path is not a file: {value}")
        return value

    return value


def get_kubeconfig_option() -> Callable[[Any], Optional[str]]:
    """Returns a pre-configured kubeconfig option for use in commands."""
    return typer.Option(
        "~/.kube/config",
        "--kubeconfig",
        "-k",
        help="Path to the kubeconfig file",
        callback=validate_kubeconfig,
        envvar="KUBECONFIG",
    )


def add_kubeconfig_flag(function):
    """Decorator to add the kubeconfig flag to a command."""
    function = typer.Option(
        None,
        "--kubeconfig",
        "-k",
        help="Path to the kubeconfig file",
        callback=validate_kubeconfig,
        envvar="KUBECONFIG",
    )(function)

    return function


def print_kubeconfig_info(kubeconfig: str):
    """Print information about the kubeconfig being used."""
    if kubeconfig:
        console.print(f"Using kubeconfig: [cyan bold]{kubeconfig}[/cyan bold]")

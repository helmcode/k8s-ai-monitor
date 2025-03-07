import typer
from typing import Optional, List
from rich.console import Console
from commands.info import show_info
from commands.pods import monitor_pods
from flags.kubeconfig import get_kubeconfig_option
from flags.namespace import get_namespace_option, process_namespaces


app = typer.Typer(
    name="kai",
    help="Kubernetes Monitor CLI",
    add_completion=True,
)


console = Console()


@app.command("info")
def info_command():
    show_info()


@app.command("pods")
def pods_command(
    kubeconfig: Optional[str] = get_kubeconfig_option(),
    namespace: Optional[List[str]] = get_namespace_option()
):
    unique_namespaces = process_namespaces(namespace)
    console.print(f"[bold]Monitoring namespaces:[/bold] {', '.join(unique_namespaces)}")
    monitor_pods(kubeconfig=kubeconfig, namespaces=unique_namespaces)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context
):
    if ctx.invoked_subcommand is None:
        console.print(
            "[bold green]Kubernetes Monitor CLI[/bold green] - "
            "[italic]Version 0.0.2[/italic]\n"
            "\n"
            "Run 'kai info' to get more information about the tool.\n"
            "\n"
            "Run 'kai --help' for usage information.\n"
        )


if __name__ == "__main__":
    app()

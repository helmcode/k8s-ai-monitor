import typer
from typing import Optional, List
from rich.console import Console
from commands.info import show_info
from commands.pods import monitor_pods
from flags.kubeconfig import get_kubeconfig_option


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
    namespace: Optional[List[str]] = typer.Option(
        ["default"],
        "--namespace", "-n",
        help="Kubernetes namespaces to monitor. Use multiple --namespace flags or comma-separated values (e.g., --namespace ns1,ns2,ns3)",
        show_default=True
    )
):
    # Process namespaces - handle comma-separated values
    processed_namespaces = []
    for ns in namespace:
        # Split by comma if present
        if "," in ns:
            processed_namespaces.extend([n.strip() for n in ns.split(",")])
        else:
            processed_namespaces.append(ns)

    # Remove duplicates while preserving order
    unique_namespaces = []
    for ns in processed_namespaces:
        if ns not in unique_namespaces:
            unique_namespaces.append(ns)

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

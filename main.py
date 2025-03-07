import typer
from typing import Optional
from rich.console import Console
from commands.info import show_info
from flags.kubeconfig import print_kubeconfig_info, get_kubeconfig_option


app = typer.Typer(
    name="kai",
    help="Kubernetes Monitor CLI",
    add_completion=True,
)


console = Console()


@app.command("info")
def info_command():
    show_info()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    kubeconfig: Optional[str] = get_kubeconfig_option()
):
    if ctx.invoked_subcommand is None:
        console.print(
            "[bold green]Kubernetes Monitor CLI[/bold green] - "
            "[italic]Version 0.0.1[/italic]\n"
        )

        print_kubeconfig_info(kubeconfig)


if __name__ == "__main__":
    app()

from typing import List
import typer
from rich.console import Console

console = Console()

def get_namespace_option():
    """
    Returns the default value for the namespace option

    Returns:
        Default value for the namespace option
    """
    return typer.Option(
        ["default"],
        "--namespace", "-n",
        help="Kubernetes namespaces to monitor. Use multiple --namespace flags or comma-separated values (e.g., --namespace ns1,ns2,ns3)",
        show_default=True
    )


def process_namespaces(namespace_list: List[str]) -> List[str]:
    """
    Process a list of namespaces, handling comma-separated values and removing duplicates

    Args:
        namespace_list: List of namespaces, potentially containing comma-separated values

    Returns:
        List of unique namespaces
    """
    # Process namespaces - handle comma-separated values
    processed_namespaces = []
    for ns in namespace_list:
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

    return unique_namespaces

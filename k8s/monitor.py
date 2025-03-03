from datetime import datetime
from typing import Dict, List, Any
from kubernetes import client, config
from utils.logging import setup_logger

logger = setup_logger(__name__)

class KubernetesMonitor:
    def __init__(self, cluster_configs):
        """
        Initializes the K8s monitor with multiple cluster configurations

        Args:
            cluster_configs: Dict[str, str] - Map of cluster name to kubeconfig path
        """
        self.clusters = {}
        for cluster_name, kubeconfig_path in cluster_configs.items():
            try:
                # Load Kubernetes configuration
                config.load_kube_config(config_file=kubeconfig_path)
                api_client = client.ApiClient()

                self.clusters[cluster_name] = {
                    "core_api": client.CoreV1Api(api_client),
                    "apps_api": client.AppsV1Api(api_client),
                    "events_api": client.EventsV1Api(api_client)
                }
                logger.info(f"Configured cluster: {cluster_name}")
            except Exception as e:
                logger.error(f"Error configuring cluster {cluster_name}: {str(e)}")

    def check_pod_health(self, cluster_name, namespace="default"):
        """
        Checks the health of pods in a specific namespace

        Args:
            cluster_name: Name of the cluster to check
            namespace: Kubernetes namespace to check

        Returns:
            List of issue dictionaries
        """
        if cluster_name not in self.clusters:
            logger.error(f"Cluster {cluster_name} not found")
            return []

        issues = []
        try:
            core_api = self.clusters[cluster_name]["core_api"]
            pods = core_api.list_namespaced_pod(namespace=namespace)

            for pod in pods.items:
                pod_name = pod.metadata.name
                pod_status = pod.status

                # Check pod phase (status)
                pod_phase = pod_status.phase
                problematic_phases = ["Pending", "Failed", "Unknown"]

                # Check for various container issues
                container_issues = {}
                for cs in (pod_status.container_statuses or []):
                    if cs.state.waiting:
                        container_issues[cs.name] = cs.state.waiting.reason
                    elif cs.state.terminated and cs.state.terminated.exit_code != 0:
                        container_issues[cs.name] = f"Terminated(ExitCode:{cs.state.terminated.exit_code})"

                # Check for specific issues
                crash_loop_back_off = any(
                    reason == "CrashLoopBackOff" for reason in container_issues.values()
                )
                image_pull_back_off = any(
                    reason == "ImagePullBackOff" for reason in container_issues.values()
                )
                create_container_error = any(
                    reason == "CreateContainerError" for reason in container_issues.values()
                )
                oom_killed = any(
                    "OOMKilled" in reason for reason in container_issues.values()
                )

                if (pod_phase in problematic_phases or
                    "Error" in pod_phase or
                    crash_loop_back_off or
                    image_pull_back_off or
                    create_container_error or
                    oom_killed):
                    # Get pod logs if possible
                    try:
                        container_name = pod.spec.containers[0].name
                        container_logs = core_api.read_namespaced_pod_log(
                            name=pod_name,
                            namespace=namespace,
                            container=container_name,
                            tail_lines=100
                        )
                    except Exception as e:
                        container_logs = f"Could not get logs: {str(e)}"

                    # Get related events
                    field_selector = f"involvedObject.name={pod_name}"
                    events = core_api.list_namespaced_event(
                        namespace=namespace,
                        field_selector=field_selector
                    )

                    event_messages = []
                    for event in events.items:
                        event_messages.append({
                            "type": event.type,
                            "reason": event.reason,
                            "message": event.message,
                            "count": event.count,
                            "first_timestamp": event.first_timestamp,
                            "last_timestamp": event.last_timestamp
                        })

                    # Determine the issue type and description
                    issue_type = "PodStatusIssue"
                    description = f"Pod is in {pod_phase} state"

                    if crash_loop_back_off:
                        issue_type = "CrashLoopBackOff"
                        description = "Pod is in CrashLoopBackOff state"
                    elif image_pull_back_off:
                        issue_type = "ImagePullBackOff"
                        description = "Pod has ImagePullBackOff error"
                    elif create_container_error:
                        issue_type = "CreateContainerError"
                        description = "Pod failed to create container"
                    elif oom_killed:
                        issue_type = "OOMKilled"
                        description = "Pod was terminated due to out of memory"
                    elif container_issues:
                        # Get the first issue if multiple exist
                        container, reason = next(iter(container_issues.items()))
                        issue_type = "ContainerError"
                        description = f"Container {container} has issue: {reason}"

                    issues.append({
                        "cluster": cluster_name,
                        "namespace": namespace,
                        "resource_type": "Pod",
                        "resource_name": pod_name,
                        "issue_type": issue_type,
                        "severity": "High",
                        "description": description,
                        "logs": container_logs,
                        "events": event_messages,
                        "detected_at": datetime.now().isoformat()
                    })

                    # Continue to next pod after reporting status issue
                    continue

                # Check container restarts
                for container_status in pod_status.container_statuses or []:
                    restart_count = container_status.restart_count
                    if restart_count > 5:  # Restart threshold

                        container_logs = core_api.read_namespaced_pod_log(
                            name=pod_name,
                            namespace=namespace,
                            container=container_status.name,
                            tail_lines=100
                        )

                        # Get related events
                        field_selector = f"involvedObject.name={pod_name}"
                        events = core_api.list_namespaced_event(
                            namespace=namespace,
                            field_selector=field_selector
                        )

                        event_messages = []
                        for event in events.items:
                            event_messages.append({
                                "type": event.type,
                                "reason": event.reason,
                                "message": event.message,
                                "count": event.count,
                                "first_timestamp": event.first_timestamp,
                                "last_timestamp": event.last_timestamp
                            })

                        issues.append({
                            "cluster": cluster_name,
                            "namespace": namespace,
                            "resource_type": "Pod",
                            "resource_name": pod_name,
                            "issue_type": "ContainerRestartIssue",
                            "severity": "Medium",
                            "description": f"Container {container_status.name} has restarted {restart_count} times",
                            "logs": container_logs,
                            "events": event_messages,
                            "detected_at": datetime.now().isoformat()
                        })

            return issues
        except Exception as e:
            logger.error(f"Error checking pods in {cluster_name}/{namespace}: {str(e)}")
            return []

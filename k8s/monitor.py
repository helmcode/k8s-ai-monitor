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

    def check_pod_health(self, cluster_name, namespace="default") -> List[Dict[str, Any]]:
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

                        events_data = []
                        for event in events.items:
                            events_data.append({
                                "type": event.type,
                                "reason": event.reason,
                                "message": event.message,
                                "count": event.count,
                                "first_timestamp": event.first_timestamp,
                                "last_timestamp": event.last_timestamp
                            })

                        # Build issue object
                        issue = {
                            "cluster": cluster_name,
                            "namespace": namespace,
                            "resource_type": "Pod",
                            "resource_name": pod_name,
                            "container": container_status.name,
                            "issue_type": "RestartLoop",
                            "details": {
                                "restart_count": restart_count,
                                "state": str(container_status.state),
                                "logs": container_logs,
                                "events": events_data
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        issues.append(issue)

                # Check for pods stuck in Pending or CrashLoopBackOff
                if pod_status.phase == "Pending" or any(
                    cs.state.waiting and cs.state.waiting.reason == "CrashLoopBackOff"
                    for cs in (pod_status.container_statuses or [])):

                    events = core_api.list_namespaced_event(
                        namespace=namespace,
                        field_selector=f"involvedObject.name={pod_name}"
                    )

                    events_data = []
                    for event in events.items:
                        events_data.append({
                            "type": event.type,
                            "reason": event.reason,
                            "message": event.message,
                            "count": event.count
                        })

                    issue = {
                        "cluster": cluster_name,
                        "namespace": namespace,
                        "resource_type": "Pod",
                        "resource_name": pod_name,
                        "issue_type": "DeploymentIssue",
                        "details": {
                            "phase": pod_status.phase,
                            "conditions": str(pod_status.conditions),
                            "events": events_data
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    issues.append(issue)

            return issues
        except Exception as e:
            logger.error(f"Error checking pods in {cluster_name}/{namespace}: {str(e)}")
            return []

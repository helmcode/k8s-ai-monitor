import asyncio
from utils.logging import setup_logger
from config.env import ENV, get_cluster_configs
from k8s.monitor import KubernetesMonitor
from notifications.slack import SlackNotifier
from llm.processor import LLMProcessor

logger = setup_logger()

class KubernetesAssistant:
    def __init__(self, cluster_configs, slack_token, llm_api_key, check_interval=300):
        """
        Initializes the Kubernetes assistant

        Args:
            cluster_configs: Dict[str, str] - Cluster configurations
            slack_token: Token for Slack notifications
            llm_api_key: API key for the LLM processor
            check_interval: Check interval in seconds
        """
        self.k8s_monitor = KubernetesMonitor(cluster_configs)
        self.slack_notifier = SlackNotifier(slack_token)
        self.llm_processor = LLMProcessor(llm_api_key)
        self.check_interval = check_interval

    async def process_issue(self, issue):
        """
        Processes a detected issue
        """
        logger.info(f"Processing issue in {issue['cluster']}/{issue['namespace']}/{issue['resource_name']}")

        diagnosis, recommendations = await self.llm_processor.analyze_issue(issue)

        self.slack_notifier.send_alert(
            issue=issue,
            diagnosis=diagnosis,
            recommendations=recommendations
        )

    async def monitor_all_clusters(self):
        """
        Monitors all registered clusters
        """
        while True:
            for cluster_name in self.k8s_monitor.clusters:
                namespaces = ["default", "kube-system"]

                for namespace in namespaces:
                    issues = self.k8s_monitor.check_pod_health(
                        cluster_name=cluster_name,
                        namespace=namespace
                    )

                    for issue in issues:
                        await self.process_issue(issue)

            await asyncio.sleep(self.check_interval)


if __name__ == "__main__":
    try:
        cluster_configs = get_cluster_configs()
        slack_token = ENV["SLACK_API_TOKEN"]
        llm_api_key = ENV["ANTHROPIC_API_KEY"]
        check_interval = ENV["K8S_CHECK_INTERVAL"]

        assistant = KubernetesAssistant(
            cluster_configs=cluster_configs,
            slack_token=slack_token,
            llm_api_key=llm_api_key,
            check_interval=check_interval
        )

        logger.info("Starting Kubernetes Assistant...")
        asyncio.run(assistant.monitor_all_clusters())
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        exit(1)

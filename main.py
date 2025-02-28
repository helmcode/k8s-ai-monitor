import asyncio
from utils.logging import setup_logger
from config.env import ENV
from config.yaml_config import get_check_interval, get_kubeconfigs, get_namespaces, get_slack_config
from k8s.monitor import KubernetesMonitor
from notifications.slack import SlackNotifier
from llm.processor import LLMProcessor

logger = setup_logger()

class KubernetesAssistant:
    def __init__(self, cluster_configs, slack_token, llm_api_key, check_interval=300, namespaces=None, slack_config=None):
        """
        Initializes the Kubernetes assistant

        Args:
            cluster_configs: Dict[str, str] - Cluster configurations
            slack_token: Token for Slack notifications
            llm_api_key: API key for the LLM processor
            check_interval: Check interval in seconds
            namespaces: List of namespaces to monitor
            slack_config: Slack configuration (enabled, channel)
        """
        self.k8s_monitor = KubernetesMonitor(cluster_configs)
        self.slack_config = slack_config
        self.slack_notifier = SlackNotifier(slack_token, default_channel=self.slack_config.get("channel"))
        self.llm_processor = LLMProcessor(llm_api_key)
        self.check_interval = check_interval
        self.namespaces = namespaces or ["default", "kube-system"]

    async def process_issue(self, issue):
        """
        Processes a detected issue
        """
        logger.info(f"Processing issue in {issue['cluster']}/{issue['namespace']}/{issue['resource_name']}")

        diagnosis, recommendations = await self.llm_processor.analyze_issue(issue)

        if self.slack_config.get("enabled", True):
            self.slack_notifier.send_alert(
                issue=issue,
                diagnosis=diagnosis,
                recommendations=recommendations,
                channel=self.slack_config.get("channel")
            )
        else:
            logger.info("Slack notifications are disabled. Skipping alert.")

    async def monitor_all_clusters(self):
        """
        Monitors all registered clusters
        """
        while True:
            for cluster_name in self.k8s_monitor.clusters:
                for namespace in self.namespaces:
                    issues = self.k8s_monitor.check_pod_health(
                        cluster_name=cluster_name,
                        namespace=namespace
                    )

                    for issue in issues:
                        await self.process_issue(issue)

            await asyncio.sleep(self.check_interval)


if __name__ == "__main__":
    try:
        cluster_configs = get_kubeconfigs()
        check_interval = get_check_interval()
        namespaces = get_namespaces()
        slack_config = get_slack_config()

        slack_token = ENV["SLACK_API_TOKEN"]
        llm_api_key = ENV["ANTHROPIC_API_KEY"]

        assistant = KubernetesAssistant(
            cluster_configs=cluster_configs,
            slack_token=slack_token,
            llm_api_key=llm_api_key,
            check_interval=check_interval,
            namespaces=namespaces,
            slack_config=slack_config
        )

        logger.info("Starting Kubernetes Assistant...")
        logger.info(f"Monitoring clusters: {', '.join(cluster_configs.keys())}")
        logger.info(f"Monitoring namespaces: {', '.join(namespaces)}")
        logger.info(f"Check interval: {check_interval} seconds")
        logger.info(f"Slack notifications: {'enabled' if slack_config.get('enabled', False) else 'disabled'}")
        if slack_config.get("enabled", False):
            logger.info(f"Slack channel: {slack_config.get('channel')}")

        asyncio.run(assistant.monitor_all_clusters())
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        exit(1)

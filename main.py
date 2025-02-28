import os
import time
import json
import logging
from kubernetes import client, config
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Logging configuration
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("k8s-mcp")

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
                # Corregir la forma de cargar la configuración de Kubernetes
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
                
                # Check for container restarts
                for container_status in pod_status.container_statuses or []:
                    restart_count = container_status.restart_count
                    if restart_count > 5:  # Restart threshold
                        # Get container logs
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

class SlackNotifier:
    def __init__(self, token, default_channel="#tests"):
        """
        Initializes the Slack notifier
        
        Args:
            token: Slack API token
            default_channel: Default channel for alerts
        """
        self.client = WebClient(token=token)
        self.default_channel = default_channel
    
    def send_alert(self, issue, diagnosis, recommendations, channel=None):
        """
        Sends an alert about a Kubernetes issue
        
        Args:
            issue: Object with issue details
            diagnosis: Analysis generated by the LLM
            recommendations: Recommendations generated by the LLM
            channel: Slack channel (optional)
        """
        if not channel:
            channel = self.default_channel
        
        try:
            # Generate blocks for rich message
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"⚠️ Kubernetes Alert: {issue['resource_type']} {issue['resource_name']}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Cluster:*\n{issue['cluster']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Namespace:*\n{issue['namespace']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Type:*\n{issue['issue_type']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Detected:*\n{issue['timestamp']}"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Diagnosis:*\n{diagnosis}"
                    }
                }
            ]
            
            # Add recommendations
            if recommendations:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Recommendations:*\n{recommendations}"
                    }
                })
            
            # Add relevant details if logs are available
            if "logs" in issue["details"] and issue["details"]["logs"]:
                # Take only the last 5 lines to avoid saturation
                logs = issue["details"]["logs"].strip().split("\n")[-5:]
                log_text = "\n".join(logs)
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Relevant logs:*\n```{log_text}```"
                    }
                })
            
            # Send message to Slack
            response = self.client.chat_postMessage(
                channel=channel,
                text=f"Kubernetes Alert: {issue['issue_type']} in {issue['resource_name']}",
                blocks=blocks
            )
            logger.info(f"Alert sent to Slack: {response['ts']}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Error sending alert to Slack: {str(e)}")
            return False

class LLMProcessor:
    def __init__(self, api_key, endpoint="https://api.anthropic.com/v1/messages"):
        """
        Initializes the LLM processor for analysis
        
        Args:
            api_key: API key for the LLM service
            endpoint: API endpoint
        """
        self.api_key = api_key
        self.endpoint = endpoint
    
    async def analyze_issue(self, issue):
        """
        Analyzes an issue using the LLM
        
        Args:
            issue: Object with issue details
        
        Returns:
            tuple: (diagnosis, recommendations)
        """
        try:
            # Prepare the message for the LLM
            resource_type = issue["resource_type"]
            resource_name = issue["resource_name"]
            issue_type = issue["issue_type"]
            
            # Extract relevant information for context
            details = issue["details"]
            logs_excerpt = ""
            if "logs" in details and details["logs"]:
                logs = details["logs"].strip().split("\n")
                logs_excerpt = "\n".join(logs[-20:])  # Last 20 lines
            
            events_data = ""
            if "events" in details and details["events"]:
                for event in details["events"][:5]:  # First 5 events
                    events_data += f"- {event.get('type', '')}: {event.get('reason', '')} - {event.get('message', '')}\n"
            
            # Build the prompt for the LLM
            prompt = f"""
            Analyze the following issue in a Kubernetes cluster:
            
            Resource: {resource_type} "{resource_name}" in namespace "{issue['namespace']}"
            Cluster: {issue['cluster']}
            Issue type: {issue_type}
            
            Additional details:
            {json.dumps(details, indent=2, default=str)}
            
            Related events:
            {events_data}
            
            Logs (excerpt):
            ```
            {logs_excerpt}
            ```
            
            Please provide:
            1. A clear and concise diagnosis of the issue
            2. Specific recommendations to resolve the issue
            """
            
            # Call Claude API
            headers = {
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                "x-api-key": self.api_key
            }
            
            payload = {
                "model": "claude-3-7-sonnet-20250219",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1024,
                "temperature": 0.1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        llm_response = result["content"][0]["text"]
                        
                        # Extract diagnosis and recommendations
                        diagnosis_marker = "diagnosis"
                        recommendation_marker = "recommendations"
                        
                        # Try to split the response
                        parts = llm_response.lower().split(recommendation_marker)
                        
                        if len(parts) >= 2:
                            diagnosis_part = parts[0]
                            recommendations_part = recommendation_marker + parts[1]
                            
                            # Clean up the diagnosis
                            if diagnosis_marker in diagnosis_part:
                                diagnosis = diagnosis_part.split(diagnosis_marker)[1].strip()
                            else:
                                diagnosis = diagnosis_part.strip()
                            
                            recommendations = recommendations_part.strip()
                        else:
                            # Fallback
                            diagnosis = llm_response
                            recommendations = ""
                        
                        return diagnosis, recommendations
                    else:
                        error_text = await response.text()
                        logger.error(f"Error in LLM API: {response.status} - {error_text}")
                        return (
                            f"Could not analyze the issue (Error {response.status})",
                            "Review logs and events manually."
                        )
        
        except Exception as e:
            logger.error(f"Error processing with LLM: {str(e)}")
            return (
                "Error processing the issue with LLM",
                "Review manually or try again later."
            )

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
        
        # Analyze with LLM
        diagnosis, recommendations = await self.llm_processor.analyze_issue(issue)
        
        # Send notification to Slack
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
                # Check all important namespaces
                namespaces = ["default", "kube-system", "production", "staging"]
                
                for namespace in namespaces:
                    issues = self.k8s_monitor.check_pod_health(
                        cluster_name=cluster_name,
                        namespace=namespace
                    )
                    
                    # Process each detected issue
                    for issue in issues:
                        await self.process_issue(issue)
            
            # Wait until the next cycle
            await asyncio.sleep(self.check_interval)

# Example usage
if __name__ == "__main__":
    # Configuration
    cluster_configs = {
        # "production": "~/.kube/config-prod",
        "dev": "~/.kube/anyformat/dev"
    }

    slack_token = os.getenv("SLACK_API_TOKEN")
    llm_api_key = os.getenv("ANTHROPIC_API_KEY")

    if not slack_token or not llm_api_key:
        logger.error("Required environment variables: SLACK_API_TOKEN, ANTHROPIC_API_KEY")
        exit(1)

    # Start the assistant
    assistant = KubernetesAssistant(
        cluster_configs=cluster_configs,
        slack_token=slack_token,
        llm_api_key=llm_api_key,
        check_interval=300  # 5 minutes
    )

    # Run the monitor
    asyncio.run(assistant.monitor_all_clusters())

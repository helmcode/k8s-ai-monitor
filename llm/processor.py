import json
import aiohttp
from typing import Dict, Any, Tuple
from utils.logging import setup_logger

logger = setup_logger(__name__)

class LLMProcessor:
    def __init__(self, api_key, endpoint="https://api.anthropic.com/v1/messages"):
        self.api_key = api_key
        self.endpoint = endpoint

    async def analyze_issue(self, issue: Dict[str, Any]) -> Tuple[str, str]:
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

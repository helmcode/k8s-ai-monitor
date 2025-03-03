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
            description = issue.get("description", "No description provided")

            # Extract relevant information for context
            logs_excerpt = issue.get("logs", "")
            if logs_excerpt and isinstance(logs_excerpt, str):
                logs_excerpt = logs_excerpt[-1000:] if len(logs_excerpt) > 1000 else logs_excerpt
            else:
                logs_excerpt = "No logs available"

            # Extract events
            events = issue.get("events", [])
            events_text = ""
            for event in events:
                events_text += f"Type: {event.get('type', 'N/A')}, Reason: {event.get('reason', 'N/A')}, Message: {event.get('message', 'N/A')}\n"

            # Prepare the message for Claude
            prompt = f"""
            As a Kubernetes expert, analyze this issue and provide a VERY CONCISE diagnosis and recommendations.

            Your response will be displayed in Slack, so:
            1. Keep your diagnosis under 200 characters if possible
            2. Provide no more than 3 specific, actionable recommendations
            3. Use simple formatting that works in Slack (basic markdown)
            4. Do not use complex formatting, tables, or code blocks longer than 3 lines
            5. Be direct and to the point

            ISSUE DETAILS:
            - Resource Type: {resource_type}
            - Resource Name: {resource_name}
            - Issue Type: {issue_type}
            - Description: {description}

            LOGS:
            ```
            {logs_excerpt}
            ```

            EVENTS:
            ```
            {events_text}
            ```

            Format your response exactly like this:
            Diagnosis: [1-2 sentences explaining the root cause]

            Recommendations:
            • [First recommendation]
            • [Second recommendation]
            • [Third recommendation]
            """

            # Send the request to Claude
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            data = {
                "model": "claude-3-7-sonnet-latest",
                "max_tokens": 1000,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, headers=headers, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from LLM API: {error_text}")
                        return "Error processing with LLM", "Please check the logs for details"

                    response_data = await response.json()
                    response_text = response_data["content"][0]["text"]

                    # Split the response into diagnosis and recommendations
                    parts = response_text.split("Recommendations:")
                    if len(parts) > 1:
                        diagnosis = parts[0].replace("Diagnosis:", "").strip()
                        recommendations = parts[1].strip()
                    else:
                        diagnosis = response_text
                        recommendations = "No specific recommendations provided"

                    return diagnosis, recommendations

        except Exception as e:
            logger.error(f"Error processing with LLM: {str(e)}")
            return f"Error processing with LLM: {str(e)}", "Please check the logs for details"

import os
import asyncio
from typing import Dict, Any, Tuple
from anthropic import AsyncAnthropic


class ClaudeAnalyzer:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable or pass it to the constructor.")

        self.client = AsyncAnthropic(api_key=self.api_key)
        self.model = "claude-3-7-sonnet-latest"

    async def analyze_issue(self, issue: Dict[str, Any]) -> Dict[str, str]:
        """
        Analyzes an issue using Claude and provides diagnosis and recommendations

        Args:
            issue: Object with issue details

        Returns:
            Dict with diagnosis and recommendations
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

            # Prepare the prompt for Claude
            prompt = f"""
            As a Kubernetes expert, analyze this issue and provide a VERY CONCISE diagnosis and recommendations.

            Your response will be displayed in the terminal, so:
            1. Keep your diagnosis under 200 characters if possible
            2. Provide no more than 3 specific, actionable recommendations
            3. Use simple formatting
            4. Be direct and to the point

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
            Diagnosis: [2-3 sentences explaining the root cause]

            Recommendations:
            • [First recommendation]
            • [Second recommendation]
            • [Third recommendation]
            • [Fourth recommendation]
            • [Fifth recommendation]
            """

            # Send the request to Claude
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text

            # Split the response into diagnosis and recommendations
            parts = response_text.split("Recommendations:")
            if len(parts) > 1:
                diagnosis = parts[0].replace("Diagnosis:", "").strip()
                recommendations = parts[1].strip()
            else:
                diagnosis = response_text
                recommendations = "No specific recommendations provided"

            return {
                "diagnosis": diagnosis,
                "recommendations": recommendations
            }

        except Exception as e:
            error_message = f"Error processing with Claude: {str(e)}"
            return {
                "diagnosis": error_message,
                "recommendations": "Please check the logs for details"
            }

    def analyze_issue_sync(self, issue: Dict[str, Any]) -> Dict[str, str]:
        """
        Synchronous wrapper for analyze_issue

        Args:
            issue: Object with issue details

        Returns:
            Dict with diagnosis and recommendations
        """
        return asyncio.run(self.analyze_issue(issue))

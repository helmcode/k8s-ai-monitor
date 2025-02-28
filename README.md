# Kubernetes Assistant

![Architecture](./svg/architecture.svg)

## Overview
The Kubernetes Assistant is an advanced monitoring tool that connects to your Kubernetes clusters to:

- Diagnose pod and service issues through log and event analysis
- Recommend optimal resource configurations based on usage patterns
- Provide intelligent alerts via Slack with actionable recommendations
- Detect inefficient or insecure configurations

## Features
- **Multi-cluster monitoring**: Connect to and monitor multiple Kubernetes clusters simultaneously
- **Intelligent analysis**: Uses Claude 3.7 Sonnet LLM to analyze issues and provide human-readable diagnoses
- **Actionable recommendations**: Provides specific recommendations to resolve detected issues
- **Slack integration**: Sends formatted alerts with relevant context to Slack channels

## Project Structure
```
kubernetes-monitor/
├── config/             # Configuration management
├── k8s/                # Kubernetes monitoring logic
├── llm/                # LLM processing for analysis
├── notifications/      # Notification services (Slack)
├── utils/              # Utility functions
├── main.py             # Main application entry point
├── requirements.txt    # Project dependencies
├── setup.yaml          # YAML configuration file
└── README.md           # This file
```

## Setup

### Prerequisites
- Python 3.12+
- Access to Kubernetes clusters
- Slack workspace with bot permissions
- Anthropic API key for Claude

### Slack Setup
1. Create a Slack app in your workspace
2. Add the following Bot Token Scopes:
   - `chat:write`
3. Install the app to your workspace
4. Invite the bot to the channels where you want to receive alerts

### Environment Variables
Export the following variables:
```
export ANTHROPIC_API_KEY="your-api-key"
export SLACK_API_TOKEN="your-slack-token"
```

### Configuration File
The application uses a YAML configuration file (`setup.yaml`) with the following structure:
```yaml
monitor:
  check_interval: 300  # Interval in seconds between checks
  notifications:
    - slack:
        enabled: true
        channel: "#tests"  # Slack channel for notifications

kubernetes:
  namespaces: [default, kube-system]  # Namespaces to monitor
  kubeconfigs:
    development:  # Cluster name
      path: ~/.kube/dev  # Path to kubeconfig file
    production:   # Cluster name
      path: ~/.kube/prod  # Path to kubeconfig file
```

### Installation
1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Export environment variables
4. Create a `setup.yaml` file with your configuration
5. Run the application:
   ```
   python main.py
   ```

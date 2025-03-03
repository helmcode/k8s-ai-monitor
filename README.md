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

if your hace EKS clusters, you need configure AWS CLI or export the following variables:
```
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_REGION="your-region"
```

### Configuration File
The application uses a YAML configuration file (`setup.yaml`). Rename `example.setup.yaml` to `setup.yaml`.
```
mv example.setup.yaml setup.yaml
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

## Monitored Kubernetes Issues

The Kubernetes Assistant monitors the following types of issues:

### Pod Status Issues
- **CrashLoopBackOff**: Pods that continuously crash and restart
- **ImagePullBackOff**: Pods that fail to pull their container images
- **CreateContainerError**: Pods that fail during container creation
- **OOMKilled**: Pods terminated due to out-of-memory conditions
- **Terminated with Error**: Containers that exit with non-zero status codes
- **Pending/Failed/Unknown**: Pods stuck in problematic phases

### Resource Issues
- **Container Restarts**: Containers that have excessive restart counts
- **Resource Constraints**: Pods hitting CPU/memory limits

### Event Analysis
The assistant analyzes pod events to provide context about:
- Scheduling problems
- Node-related issues
- Volume mount failures
- Security context issues

Every issue is analyzed by Claude 3.7 Sonnet to provide human-readable diagnoses and actionable recommendations, helping you resolve problems quickly and effectively.

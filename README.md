# Kubernetes Monitor CLI (kai)

![Architecture](./svg/architecture.svg)

## Overview
Kubernetes Monitor CLI (kai) is a powerful command-line tool that helps you diagnose and troubleshoot Kubernetes clusters:

- Monitor pod health across multiple namespaces
- Diagnose pod issues with AI-powered analysis
- Get actionable recommendations for resolving common Kubernetes problems
- View relevant logs and events in a structured format

## Features
- **Command-line interface**: Simple and intuitive CLI for monitoring Kubernetes resources
- **Multi-namespace monitoring**: Monitor pods across one or more namespaces
- **AI-powered analysis**: Uses Claude 3.7 Sonnet to analyze issues and provide human-readable diagnoses
- **Rich terminal output**: Structured and color-coded display of issues, logs, and events
- **Custom kubeconfig support**: Specify custom kubeconfig paths for different environments


## Installation

### Prerequisites
- Python 3.9+
- Access to Kubernetes clusters
- Anthropic API key (optional, for AI-powered analysis)

### Setup
1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. (Optional) Set environment variables for AI analysis:
   ```
   export ANTHROPIC_API_KEY="your-api-key"
   ```

### Usage
Run the CLI tool directly:
```
python main.py [command] [options]
```

Or create an alias for easier access:
```
alias kai="python /path/to/main.py"
```

Or compile the application:
```
pyinstaller main.spec
ln -s dist/main/main /usr/local/bin/kai
```

## Commands

### info
Display information about the tool and available commands.
```
kai info
```

### pods
Monitor pod health in specified namespaces.
```
kai pods [--kubeconfig PATH] [--namespace NAMESPACE1,NAMESPACE2]
```

Options:
- `--kubeconfig, -k`: Path to the kubeconfig file (defaults to `~/.kube/config`)
- `--namespace, -n`: Kubernetes namespaces to monitor (defaults to `default`)

## Monitored Kubernetes Issues

Kubernetes Monitor CLI tracks the following types of pod issues:

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

### AI Analysis
When an Anthropic API key is provided, each issue is analyzed by Claude 3.7 Sonnet to provide:
- Concise diagnosis of the root cause
- Specific, actionable recommendations to resolve the issue
- Context-aware analysis based on pod logs and events

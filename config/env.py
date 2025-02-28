import os
from typing import Dict
from utils.logging import setup_logger

logger = setup_logger(__name__)

ENV = {
    "SLACK_API_TOKEN": os.getenv("SLACK_API_TOKEN", ""),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
    "K8S_DEV_CONFIG": os.getenv("K8S_DEV_CONFIG", "~/.kube/config"),
    "K8S_CHECK_INTERVAL": int(os.getenv("K8S_CHECK_INTERVAL", "300")),
}


def validate_env() -> None:
    required_vars = ["SLACK_API_TOKEN", "ANTHROPIC_API_KEY"]

    missing_vars = []
    for var in required_vars:
        if not ENV[var]:
            missing_vars.append(var)

    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("All required environment variables are set")


try:
    validate_env()
except ValueError as e:
    logger.error(f"Environment validation failed: {str(e)}")


def get_cluster_configs() -> Dict[str, str]:
    return {"k8s": ENV["K8S_DEV_CONFIG"]}

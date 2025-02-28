import os
import yaml
from typing import Dict, List, Any
from utils.logging import setup_logger

logger = setup_logger(__name__)

CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "setup.yaml")

def load_yaml_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_FILE_PATH):
        error_msg = f"Configuration file not found: {CONFIG_FILE_PATH}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        with open(CONFIG_FILE_PATH, 'r') as file:
            config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {CONFIG_FILE_PATH}")
            return config
    except yaml.YAMLError as e:
        error_msg = f"Error parsing YAML configuration: {str(e)}"
        logger.error(error_msg)
        raise

def get_check_interval() -> int:
    try:
        config = load_yaml_config()
        return config.get('monitor', {}).get('check_interval', 300)
    except Exception as e:
        logger.warning(f"Could not get check interval from config: {str(e)}. Using default: 300")
        return 300

def get_notification_config() -> Dict[str, Any]:
    try:
        config = load_yaml_config()
        return config.get('monitor', {}).get('notifications', [])
    except Exception as e:
        logger.warning(f"Could not get notification config: {str(e)}. Using empty config.")
        return []

def get_slack_config() -> Dict[str, Any]:
    try:
        notifications = get_notification_config()
        for notification in notifications:
            if 'slack' in notification:
                return notification['slack']

        # Default configuration if not found
        return {"enabled": False, "channel": "#general"}
    except Exception as e:
        logger.warning(f"Could not get Slack config: {str(e)}. Using default config.")
        return {"enabled": False, "channel": "#general"}

def get_namespaces() -> List[str]:
    try:
        config = load_yaml_config()
        namespaces = config.get('kubernetes', {}).get('namespaces', ['default'])
        return namespaces
    except Exception as e:
        logger.warning(f"Could not get namespaces from config: {str(e)}. Using default: ['default']")
        return ['default']

def get_kubeconfigs() -> Dict[str, str]:
    try:
        config = load_yaml_config()
        kubeconfigs = config.get('kubernetes', {}).get('kubeconfigs', {})

        result = {}
        for cluster_name, cluster_config in kubeconfigs.items():
            path = cluster_config.get('path')
            if path:
                if path.startswith('~'):
                    path = os.path.expanduser(path)
                result[cluster_name] = path

        if not result:
            logger.warning("No valid kubeconfigs found in configuration")

        return result
    except Exception as e:
        logger.warning(f"Could not get kubeconfigs from config: {str(e)}. Using empty config.")
        return {}

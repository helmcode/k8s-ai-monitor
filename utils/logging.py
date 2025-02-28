import logging

def setup_logger(name="k8s-mcp", level=logging.INFO):
    logger = logging.getLogger(name)

    if not logger.handlers:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    return logger

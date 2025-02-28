import logging

def setup_logger(name="k8s-mcp", level=logging.INFO):
    """
    Configure and return a logger with the specified name and level
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if handlers haven't been set up yet
    if not logger.handlers:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    return logger

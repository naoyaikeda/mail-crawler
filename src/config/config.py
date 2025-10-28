import os
from pathlib import Path

def get_config_dir():
    """_summary_
    Get the path to the config directory.
    _description_
    This function returns the path to the config directory, which is located at ~/.mail-crawler.
    If the directory does not exist, it will be created.
    Returns:
        Path: The path to the config directory.
    """
    config_dir = Path.home() / ".mail-crawler"
    if not config_dir.exists():
        os.makedirs(config_dir)
    return config_dir

import re


def safe_filename(name: str) -> str:
    """
    Removes invalid Windows filename characters
    """
    return re.sub(r'[<>:"/\\|?*]', '_', name)
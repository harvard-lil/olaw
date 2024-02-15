"""
`utils.check_env` module: Checks that required env variables are available.
"""

import os


def check_env() -> bool:
    """
    Checks that required env variables are available.
    Throws if properties are missing or unusable.
    """
    environ = os.environ

    for prop in [
        "COURT_LISTENER_API_TOKEN",
        "COURT_LISTENER_MAX_RESULTS",
        "EXTRACT_SEARCH_STATEMENT_PROMPT",
        "COURT_LISTENER_API_URL",
        "COURT_LISTENER_BASE_URL",
        "TEXT_COMPLETION_BASE_PROMPT",
        "TEXT_COMPLETION_RAG_PROMPT",
        "TEXT_COMPLETION_HISTORY_PROMPT",
    ]:
        if prop not in environ:
            raise Exception(f"env var {prop} must be defined.")

    return True

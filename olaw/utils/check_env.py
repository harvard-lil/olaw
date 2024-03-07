import os


def check_env() -> bool:
    """
    Checks that required env variables are available.
    Throws if properties are missing or unusable.
    """
    environ = os.environ

    for prop in [
        "RATE_LIMIT_STORAGE_URI",
        "API_MODELS_RATE_LIMIT",
        "API_EXTRACT_SEARCH_STATEMENT_RATE_LIMIT",
        "API_SEARCH_RATE_LIMIT",
        "API_COMPLETE_RATE_LIMIT",
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

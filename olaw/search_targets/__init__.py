SEARCH_TARGETS = ["courtlistener"]
"""
    List of of "tools" this RAG pipeline can use to pull information from.
    See details in `README.md` under "Adding new tools".
"""


class SearchTarget:
    """
    Base class for all search targets.
    Inherit this class to let OLAW use a new tool.
    """

    RESULTS_DATA_FORMAT = {
        "text": "",  # Full text
        "prompt_text": "",  # Line of text used as part of the RAG prompt to introduce this source.
        "ui_text": "",  # Line of text used as part of the UI to introduce this source.
        "ui_url": "",  # URL used to let users explore this source.
    }

    @staticmethod
    def search(search_statement: str) -> list:
        raise NotImplementedError


from .courtlistener import CourtListener  # noqa


def route_search(search_target: str, search_statement: str):
    """
    Routes a search to the right handler.
    """
    if search_target not in SEARCH_TARGETS:
        raise Exception("Invalid search target")

    search_results = []

    if search_target == "courtlistener":
        search_results = CourtListener.search(search_statement)

    return search_results

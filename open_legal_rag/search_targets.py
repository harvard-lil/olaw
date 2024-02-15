SEARCH_TARGETS = ["courtlistener"]
"""
    List of of "tools" this RAG pipeline can use to pull remote information.
    This information is:
    - Returned by /api/extract-search-statement, when the LLM decides to use this tool
    - Consumed by /api/search to process search request

    To add a search target:
    - Amend this list
    - Edit EXTRACT_SEARCH_STATEMENT_PROMPT so the LLM knows what this new search target can be used for.
    - Edit /api/search to handle queries to this new search target.
"""

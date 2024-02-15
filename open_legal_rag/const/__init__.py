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

COURTLISTENER_OPINION_DATA_FORMAT = {
    "ref_tag": "",  # IE: [1]
    "id": "",
    "case_name": "",
    "court": "",
    "absolute_url": "",
    "status": "",
    "date_filed": "",
    "text": "",
}
"""
    Data format for CourtListener Opinion info:
    - Returned by /api/search when "search_statement" is "courtlistener"
    - Consumed by /api/complete
"""

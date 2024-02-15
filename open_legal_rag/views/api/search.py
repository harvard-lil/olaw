import os
import traceback
import requests
import html2text
from flask import current_app, jsonify, request

from open_legal_rag.search_targets import SEARCH_TARGETS
from open_legal_rag.data_formats import COURTLISTENER_OPINION_DATA_FORMAT


@current_app.route("/api/search", methods=["POST"])
def post_search():
    """
    [POST] /api/search

    Runs a search statement against a legal database and returns up to X results.
    Target legal API is determined by "search_target".
    See SEARCH_TARGETS for a list of available targets.

    Accepts JSON body with the following properties, coming from `/api/extract-search-statement`:
    - "search_statement": Search statement to be used against the search target
    - "search_target": Determines the search "tool" to be used.

    Returns JSON object in the following format:
    {
      "{search_target}": [... results]
    }
    """
    input = request.get_json()
    search_statement = ""
    search_target = ""
    output = {}

    for target in SEARCH_TARGETS:
        output[target] = []

    #
    # Check that "search_statement" was provided
    #
    if "search_statement" not in input:
        return jsonify({"error": "No search statement provided."}), 400

    search_statement = str(input["search_statement"]).strip()

    if not search_statement:
        return jsonify({"error": "Search statement cannot be empty."}), 400

    #
    # Check that "search_target" was provided and valid
    #
    if "search_target" not in input:
        return jsonify({"error": "No search target provided."}), 400

    search_target = str(input["search_target"]).strip()

    if not search_target:
        return jsonify({"error": "Search target cannot be empty."}), 400

    if search_target not in SEARCH_TARGETS:
        return jsonify({"error": f"Search target can only be: {','.join(SEARCH_TARGETS)}."}), 400

    #
    # "search_target" routing
    #
    if search_target == "courtlistener":
        output["courtlistener"] = courtlistener_search(search_statement)

    return jsonify(output), 200


def courtlistener_search(search_statement: str) -> list:
    """
    Runs search_statement against the CourtListener search API.
    - Returns up to COURT_LISTENER_MAX_RESULTS results.
    - Objects in list use the COURTLISTENER_OPINION_DATA_FORMAT template.
    """
    api_url = os.environ["COURT_LISTENER_API_URL"]
    base_url = os.environ["COURT_LISTENER_BASE_URL"]
    max_results = int(os.environ["COURT_LISTENER_MAX_RESULTS"])

    search_results = None
    output = []

    #
    # Pull search results
    #
    try:
        search_results = requests.get(
            f"{api_url}search/",
            timeout=10,
            params={"type": "o", "q": search_statement},
        ).json()
    except Exception:
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": "Could not search for court opinions on Court Listener."}), 500

    #
    # Pull opinion text for the first X results
    #
    for i in range(0, max_results):
        if i > len(search_results["results"]) - 1:
            break

        opinion = dict(COURTLISTENER_OPINION_DATA_FORMAT)

        opinion_metadata = search_results["results"][i]

        opinion["ref_tag"] = i + 1
        opinion["id"] = opinion_metadata["id"]
        opinion["case_name"] = opinion_metadata["caseName"]
        opinion["court"] = opinion_metadata["court"]
        opinion["absolute_url"] = base_url + opinion_metadata["absolute_url"]
        opinion["status"] = opinion_metadata["status"]
        opinion["date_filed"] = opinion_metadata["dateFiled"]

        # Request and format opinion text
        try:
            opinion_data = requests.get(
                f"{api_url}opinions/",
                timeout=10,
                params={"id": opinion["id"]},
            ).json()

            opinion_data = opinion_data["results"][0]
            opinion["text"] = html2text.html2text(opinion_data["html"])

        except Exception:
            current_app.logger.error(f"Not data for opinion #{opinion['id']} on Court Listener.")
            current_app.logger.error(traceback.format_exc())
            continue

        output.append(opinion)

    return output

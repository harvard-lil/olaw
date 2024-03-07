import os
import traceback
from flask import current_app, jsonify, request

from olaw.utils import get_limiter
from olaw.search_targets import SEARCH_TARGETS, route_search

API_SEARCH_RATE_LIMIT = os.environ["API_SEARCH_RATE_LIMIT"]


@current_app.route("/api/search", methods=["POST"])
@get_limiter().limit(API_SEARCH_RATE_LIMIT)
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
    try:
        output[search_target] = route_search(search_target, search_statement)
    except Exception:
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": f"Could not search for court opinions on {search_target}."}), 500

    return jsonify(output), 200

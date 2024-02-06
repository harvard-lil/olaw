"""
`views.api` module: API routes controller.
"""

import os
import traceback
import uuid
import json

import requests
import html2text
from flask import current_app, jsonify, request, g
from openai import OpenAI
import ollama

from open_legal_rag.utils import list_available_models

OPINION_DATA_TEMPLATE = {
    "id": "",
    "case_name": "",
    "court": "",
    "absolute_url": "",
    "status": "",
    "date_filed": "",
    "text": "",
}
""" Data format for info returned by /api/legal/search. """


@current_app.route("/api/models")
def get_models():
    return jsonify(list_available_models()), 200


@current_app.route("/api/legal/extract-question", methods=["POST"])
def post_legal_extract_question():
    """
    Analyses a message and, if it contains a legal question, tries to generate a search statement from it.

    Accepts JSON body with the following properties:
    - "model": One of the models /api/models lists (required)
    - "message": User prompt (required)
    - "temperature": Defaults to 0.0

    Returns JSON:
    - {"search_statement": str}
    """
    available_models = list_available_models()
    input = request.get_json()
    model = ""
    message = ""
    temperature = 0.0
    prompt = os.environ["EXTRACT_LEGAL_QUERY_PROMPT"]
    output = ""
    timeout = 30

    #
    # Check that "model" was provided and is available
    #
    if "model" not in input:
        return jsonify({"error": "No model provided."}), 400

    if input["model"] not in available_models:
        return jsonify({"error": "Requested model is invalid or not available."}), 400

    model = input["model"]

    #
    # Check that "message" was provided
    #
    if "message" not in input:
        return jsonify({"error": "No message provided."}), 400

    message = str(input["message"]).strip()

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    #
    # Validate "temperature" if provided
    #
    if "temperature" in input:
        try:
            temperature = float(input["temperature"])
            assert temperature >= 0.0
        except Exception:
            return (
                jsonify({"error": "temperature must be a float superior or equal to 0.0."}),
                400,
            )

    #
    # Ask model to filter out and extract search query
    #
    prompt = f"{prompt}\n{message}"

    try:
        # Open AI
        if model.startswith("openai"):
            openai_client = OpenAI()

            response = openai_client.chat.completions.create(
                model=model.replace("openai/", ""),
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                timeout=timeout,
            )

            output = json.loads(response.model_dump_json())["choices"][0]["message"]["content"]

        # Ollama
        if model.startswith("ollama"):
            ollama_client = ollama.Client(
                host=os.environ["OLLAMA_API_URL"],
                timeout=timeout,
            )

            response = ollama_client.chat(
                model=model.replace("ollama/", ""),
                format="json",
                options={"temperature": temperature},
                messages=[{"role": "user", "content": prompt}],
            )

            output = response["message"]["content"]
    except Exception:
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": f"Could not run completion against {model}."}), 500

    # Check output format
    try:
        output = json.loads(output)
        assert "search_statement" in output  # Will raise an exception if format is invalid
        assert isinstance(output["search_statement"], str) or output["search_statement"] is None
        assert len(output.keys()) == 1
    except Exception:
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": f"{model} returned invalid JSON."}), 500

    return jsonify(output), 200


@current_app.route("/api/legal/search", methods=["POST"])
def post_legal_search():
    """
    Runs a search statement against the Court Listener API and returns up to X court opinions.

    Accepts JSON body with the following properties:
    - "search_statement": str

    Returns JSON: List of OPINION_DATA_TEMPLATE objects
    """
    input = request.get_json()
    search_statement = ""

    api_url = os.environ["COURT_LISTENER_API_URL"]
    base_url = os.environ["COURT_LISTENER_BASE_URL"]
    max_results = int(os.environ["COURT_LISTENER_MAX_RESULTS"])

    search_results = None
    output = []

    #
    # Check that "search_statement" was provided
    #
    if "search_statement" not in input:
        return jsonify({"error": "No search statement provided."}), 400

    search_statement = str(input["search_statement"]).strip()

    if not search_statement:
        return jsonify({"error": "Search statement cannot be empty."}), 400

    #
    # Search for opinions
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

        opinion = dict(OPINION_DATA_TEMPLATE)

        opinion_metadata = search_results["results"][i]
        opinion["id"] = opinion_metadata["id"]
        opinion["case_name"] = opinion_metadata["caseName"]
        opinion["court"] = opinion_metadata["court"]
        opinion["absolute_url"] = base_url + opinion_metadata["absolute_url"]
        opinion["status"] = opinion_metadata["status"]
        opinion["date_filed"] = opinion_metadata["dateFiled"]

        # Pull opinion text
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

    return jsonify(output), 200


@current_app.route("/api/complete", methods=["POST"])
def post_complete():
    return jsonify({}), 200

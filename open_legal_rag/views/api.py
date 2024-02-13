"""
`views.api` module: API routes controller.
"""

import os
import traceback
import json

import requests
import html2text
from flask import current_app, jsonify, request, Response
from openai import OpenAI
import ollama

from open_legal_rag.utils import list_available_models

SEARCH_TARGETS = ["courtlistener"]
"""
    List of valid values for "search_target" as returned by /api/legal/extract-search-statement.
    A future version of the Open Legal RAG should include more search targets.
"""

COURT_LISTENER_OPINION_DATA_TEMPLATE = {
    "id": "",
    "case_name": "",
    "court": "",
    "absolute_url": "",
    "status": "",
    "date_filed": "",
    "text": "",
}
""" Data format for CourtListener info returned by /api/legal/search. """


@current_app.route("/api/models")
def get_models():
    """
    [GET] /api/models

    Returns a list of available / suitable text completion models.
    """
    return jsonify(list_available_models()), 200


@current_app.route("/api/legal/extract-search-statement", methods=["POST"])
def post_legal_extract_question():
    """
    [POST] /api/legal/extract-search-statement

    Analyses a message and, if it contains a legal question:
    - Indicate what API is best suited for that query
    - Returns a search statement for said API.

    Accepts JSON body with the following properties:
    - "model": One of the models /api/models lists (required)
    - "message": User prompt (required)
    - "temperature": Defaults to 0.0

    Returns JSON:
    - {"search_target": str, "search_statement": str}
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
        assert isinstance(output["search_target"], str) or output["search_target"] is None
        assert len(output.keys()) == 2
    except Exception:
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": f"{model} returned invalid JSON."}), 500

    return jsonify(output), 200


@current_app.route("/api/legal/search", methods=["POST"])
def post_legal_search():
    """
    [POST] /api/legal/search

    Runs a search statement against a legal database API and returns up to X results.
    Target legal API is determined by "search_target".
    See SEARCH_TARGETS for a list of available targets.

    Accepts JSON body with the following properties:
    - "search_statement": str
    - "search_target": str

    Returns JSON object in the following format:
    {
      "courtlistener": [] // List of COURT_LISTENER_OPINION_DATA_TEMPLATE objects
    }
    """
    input = request.get_json()
    search_statement = ""
    search_target = ""

    api_url = os.environ["COURT_LISTENER_API_URL"]
    base_url = os.environ["COURT_LISTENER_BASE_URL"]
    max_results = int(os.environ["COURT_LISTENER_MAX_RESULTS"])

    search_results = None
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
    # Check that "search_target" was provided
    #
    if "search_target" not in input:
        return jsonify({"error": "No search target provided."}), 400

    search_target = str(input["search_target"]).strip()

    if not search_target:
        return jsonify({"error": "Search target cannot be empty."}), 400

    if search_target not in SEARCH_TARGETS:
        return jsonify({"error": f"Search target can only be: {','.join(SEARCH_TARGETS)}."}), 400

    #
    # Handle "courtlistener" search target
    #
    if search_target == "courtlistener":
        try:
            search_results = requests.get(
                f"{api_url}search/",
                timeout=10,
                params={"type": "o", "q": search_statement},
            ).json()
        except Exception:
            current_app.logger.error(traceback.format_exc())
            return jsonify({"error": "Could not search for court opinions on Court Listener."}), 500

        # Pull opinion text for the first X results
        for i in range(0, max_results):
            if i > len(search_results["results"]) - 1:
                break

            opinion = dict(COURT_LISTENER_OPINION_DATA_TEMPLATE)

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
                current_app.logger.error(
                    f"Not data for opinion #{opinion['id']} on Court Listener."
                )
                current_app.logger.error(traceback.format_exc())
                continue

            output["courtlistener"].append(opinion)

    return jsonify(output), 200


@current_app.route("/api/complete", methods=["POST"])
def post_complete():
    """
    [POST] /api/complete

    Accepts JSON body with the following properties:
    - "message": User prompt (required)
    - "model": One of the models /api/models lists (required)
    - "temperature": Defaults to 0.0
    - "search_results": Output from /api/legal/search.
    - "max_tokens": If provided, caps number of tokens that will be generated in response.
    - "history": A list of chat completion objects representing the chat history. Each object must contain "user" and "content".

    Example of a "history" list:
    ```
    [
        {"role": "user", "content": "Foo bar"},
        {"role": "assistant", "content": "Bar baz"}
    ]
    ```
    """
    available_models = list_available_models()

    input = request.get_json()
    model = None
    message = None
    search_results = {}
    temperature = 0.0
    max_tokens = None

    prompt = os.environ["TEXT_COMPLETION_BASE_PROMPT"]  # Contains {history} and {rag}
    rag_prompt = os.environ["TEXT_COMPLETION_RAG_PROMPT"]  # Template for {rag}
    history_prompt = os.environ["TEXT_COMPLETION_HISTORY_PROMPT"]  # Template for {history}

    history = []  # Chat completion objects keeping track of exchanges

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
    # Validate "search_results" if provided
    #
    if "search_results" in input:
        try:
            # Validate format for courtlistener entries
            for result in input["search_results"]["courtlistener"]:
                assert set(result.keys()) == set(COURT_LISTENER_OPINION_DATA_TEMPLATE.keys())

            search_results = input["search_results"]
        except Exception:
            return (
                jsonify({"error": "search_results must be the output of /api/legal/search."}),
                400,
            )

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
    # Validate "max_tokens" if provided
    #
    if "max_tokens" in input:
        try:
            max_tokens = int(input["max_tokens"])
            assert max_tokens > 0
        except Exception:
            return (jsonify({"error": "max_tokens must be an int superior to 0."}), 400)

    #
    # Validate "history" if provided
    #
    if "history" in input:
        try:
            for past_message in input["history"]:
                assert past_message["role"]
                assert past_message["content"]
                history.append(past_message)

        except Exception:
            return (
                jsonify({"error": "past_messages must be an array of chat completion objects."}),
                400,
            )

    #
    # Assemble prompt
    #
    history_txt = ""
    search_results_txt = ""

    # History
    for past_message in history:
        history_txt += f"{past_message['role']}: {past_message['content']}\n"

    if history_txt:
        history_prompt = history_prompt.replace("{history}", history_txt)
        prompt = prompt.replace("{history}", history_prompt)
    else:
        prompt = prompt.replace("{history}", "")

    #
    # Context
    #

    # Prepare "courtlistener" search results
    if "courtlistener" in search_results and search_results["courtlistener"]:
        for result in search_results["courtlistener"]:
            case_name, date_filed, court, absolute_url = (
                result["case_name"],
                result["date_filed"],
                result["court"],
                result["absolute_url"],
            )

            absolute_url = os.environ["COURT_LISTENER_BASE_URL"] + absolute_url

            search_results_txt += (
                f"{case_name} ({date_filed[0:4]}) {court} as sourced from {absolute_url}:\n"
            )

            search_results_txt += result["text"]
            search_results_txt += "\n\n"

    if search_results_txt:
        rag_prompt = rag_prompt.replace("{rag}", search_results_txt)
        prompt = prompt.replace("{rag}", rag_prompt)
    else:
        prompt = prompt.replace("{rag}", "")

    # Message
    prompt = prompt.replace("{request}", message)

    prompt = prompt.strip()

    #
    # Run completion
    #
    try:
        # Open AI
        if model.startswith("openai"):
            openai_client = OpenAI()

            stream = openai_client.chat.completions.create(
                model=model.replace("openai/", ""),
                temperature=temperature,
                max_tokens=max_tokens if max_tokens else None,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )

            def generate_openai():
                for chunk in stream:
                    yield chunk.choices[0].delta.content or ""

            return Response(generate_openai(), mimetype="text/plain")

        # Ollama
        if model.startswith("ollama"):

            ollama_client = ollama.Client(host=os.environ["OLLAMA_API_URL"])

            stream = ollama_client.chat(
                model=model.replace("ollama/", ""),
                options={"temperature": temperature},
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )

            def generate_ollama():
                for chunk in stream:
                    yield chunk["message"]["content"] or ""

            return Response(generate_ollama(), mimetype="text/plain")
    except Exception:
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": f"Could not run completion against {model}."}), 500

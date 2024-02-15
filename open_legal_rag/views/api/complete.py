import os
import traceback

from flask import current_app, jsonify, request, Response
from openai import OpenAI
import ollama

from open_legal_rag.utils import list_available_models
from open_legal_rag.const import SEARCH_TARGETS, COURTLISTENER_OPINION_DATA_FORMAT


@current_app.route("/api/complete", methods=["POST"])
def post_complete():
    """
    [POST] /api/complete

    Accepts JSON body with the following properties:
    - "message": User prompt (required)
    - "model": One of the models /api/models lists (required)
    - "temperature": Defaults to 0.0
    - "search_results": Output from /api/search.
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
            # Top-level keys must e part of SEARCH_TARGETS
            for key in input["search_results"].keys():
                assert key in SEARCH_TARGETS

            # Validate format for "courtlistener" entries
            if "courtlistener" in input["search_results"].keys():
                for result in input["search_results"]["courtlistener"]:
                    assert set(result.keys()) == set(COURTLISTENER_OPINION_DATA_FORMAT.keys())

            search_results = input["search_results"]
        except Exception:
            return (
                jsonify({"error": "search_results must be the output of /api/search."}),
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
    if "max_tokens" in input and input["max_tokens"] is not None:
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
    # Assemble shell prompt
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
    # Assemble context
    #

    # Prepare "courtlistener" search results
    if "courtlistener" in search_results and search_results["courtlistener"]:
        for result in search_results["courtlistener"]:
            ref_tag, case_name, date_filed, court, absolute_url = (
                result["ref_tag"],
                result["case_name"],
                result["date_filed"],
                result["court"],
                result["absolute_url"],
            )

            absolute_url = os.environ["COURT_LISTENER_BASE_URL"] + absolute_url

            search_results_txt += f"[{ref_tag}] {case_name} ({date_filed[0:4]}) {court} as sourced from {absolute_url}:\n"  # noqa
            search_results_txt += result["text"]
            search_results_txt += "\n\n"

    if search_results_txt:
        rag_prompt = rag_prompt.replace("{context}", search_results_txt)
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

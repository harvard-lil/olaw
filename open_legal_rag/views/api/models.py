from flask import current_app, jsonify
from openai import OpenAI

from open_legal_rag.utils import list_available_models


@current_app.route("/api/models")
def get_models():
    """
    [GET] /api/models

    Returns a JSON list of available / suitable text completion models.
    """
    return jsonify(list_available_models()), 200

"""
`views.api` module: API routes controller.
"""
import os
import traceback
import uuid

import litellm
from flask import current_app, jsonify, request, g

from open_legal_rag.utils import list_available_models

litellm.telemetry = False


@current_app.route("/api/models")
def get_models():
    return jsonify(list_available_models()), 200


@current_app.route("/api/legal/extract-question")
def post_legal_extract_question():
    return jsonify({}), 200

@current_app.route("/api/legal/search")
def post_legal_search():
    return jsonify({}), 200

@current_app.route("/api/complete")
def post_complete():
    return jsonify({}), 200


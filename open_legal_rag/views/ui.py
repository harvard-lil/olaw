"""
`views.ui` module: UI routes controller.
"""

import os

from flask import current_app, render_template

from open_legal_rag.utils import list_available_models


@current_app.route("/")
def get_root():
    available_models = list_available_models()

    best_default_model = ""

    # Select best default model
    if "openai/gpt-4-turbo-preview" in available_models:
        best_default_model = "openai/gpt-4-turbo-preview"

    if not best_default_model:
        for model in available_models:
            if model.startswith("ollama/mixtral"):
                best_default_model = model

    return (
        render_template(
            "index.html",
            available_models=available_models,
            best_default_model=best_default_model,
        ),
        200,
    )

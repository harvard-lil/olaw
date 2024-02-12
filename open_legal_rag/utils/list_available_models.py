"""
`utils.list_available_models` module: Checks what models LiteLLM has access to.
"""

import os
import traceback

from flask import current_app
from openai import OpenAI
import ollama


def list_available_models() -> list:
    """
    Returns a list of the models Ollama and/or OpenAI can talk to based on current environment.
    """
    models = []

    if os.environ.get("OPENAI_API_KEY"):
        try:
            openai_client = OpenAI()

            for model in openai_client.models.list().data:
                if model.id.startswith("gpt-4"):
                    models.append(f"openai/{model.id}")

        except Exception:
            current_app.logger.error("Could not list Open AI models.")
            current_app.logger.error(traceback.format_exc())

    if os.environ.get("OLLAMA_API_URL"):
        try:
            ollama_client = ollama.Client(host=os.environ["OLLAMA_API_URL"])

            for model in ollama_client.list()["models"]:
                models.append(f"ollama/{model['name']}")

        except Exception:
            current_app.logger.error("Could not list Ollama models.")
            current_app.logger.error(traceback.format_exc())

    return models

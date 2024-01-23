"""
`open_legal_rag` module: REST API and CLI commands for the `open-legal-rag` pipeline.
"""
import os

from dotenv import load_dotenv
from flask import Flask

from open_legal_rag import utils


load_dotenv()

# TODO
COLD_CASES_RECORD_DATA = {}
""" Shape of the data we extract and store from COLD Cases records. """


def create_app():
    """
    App factory (https://flask.palletsprojects.com/en/2.3.x/patterns/appfactories/)
    """
    app = Flask(__name__)

    # Note: Every module in this app assumes the app context is available and initialized.
    with app.app_context():
        utils.check_env()

        os.makedirs(os.environ["VECTOR_SEARCH_PATH"], exist_ok=True)

        from open_legal_rag import commands

        # from open_legal_rag import views

        return app

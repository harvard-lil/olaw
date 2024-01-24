"""
`open_legal_rag` module: REST API and CLI commands for the `open-legal-rag` pipeline.
"""
import os

from dotenv import load_dotenv
from flask import Flask

from open_legal_rag import utils


load_dotenv()

COLD_CASES_OPINION_DATA = {
    "case_id": "",
    "case_date_filed": "",
    "case_name": "",
    "case_judges": "",
    "case_attorneys": "",
    "court_name": "",
    "court_type": "",
    "court_jurisdiction": "",
    "opinion_id": "",
    "opinion_author": "",
    "opinion_text": "",
}
"""
    Shape of the data we extract and store from COLD Cases records.
    More info: https://huggingface.co/datasets/harvard-lil/cold-cases
"""

COLD_CASES_JURISDICTION_CODES = {
    "F": "Federal Appellate",
    "FD": "Federal District",
    "FB": "Federal Bankruptcy",
    "FBP": "Federal Bankruptcy Panel",
    "FS": "Federal Special",
    "S": "State Supreme",
    "SA": "State Appellate",
    "ST": "State Trial",
    "SS": "State Special",
    "TRS": "Tribal Supreme",
    "TRA": "Tribal Appellate",
    "TRT": "Tribal Trial",
    "TRX": "Tribal Special",
    "TS": "Territory Supreme",
    "TA": "Territory Appellate",
    "TT": "Territory Trial",
    "TSP": "Territory Special",
    "SAG": "State Attorney General",
    "MA": "Military Appellate",
    "MT": "Military Trial",
    "C": "Committee",
    "I": "International",
    "T": "Testing",
}
""" Hashmap which can be used to associate jurisdiction types shortcodes to their full names. """


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

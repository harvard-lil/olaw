from dotenv import load_dotenv
from flask import Flask, make_response, jsonify

from olaw import utils

load_dotenv()


def create_app():
    """
    App factory (https://flask.palletsprojects.com/en/2.3.x/patterns/appfactories/)
    """
    app = Flask(__name__)

    # Note: Every module in this app assumes the app context is available and initialized.
    with app.app_context():
        utils.check_env()

        from olaw import views

        @app.errorhandler(429)
        def ratelimit_handler(e):
            return make_response(jsonify(error=f"Rate limit exceeded ({e.description})"), 429)

        return app

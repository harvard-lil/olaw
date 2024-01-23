""" WSGI hook """
from open_legal_rag import create_app

if __name__ == "__main__":
    create_app().run()

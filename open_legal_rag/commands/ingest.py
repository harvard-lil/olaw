"""
`commands.ingest` module: Controller for the `ingest` CLI command.
"""
import os
import glob
import traceback
import io
from shutil import rmtree

import click
import chromadb
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from flask import current_app

from open_legal_rag import COLD_CASES_RECORD_DATA


@current_app.cli.command("ingest")
def ingest() -> None:
    """
    Generates embeddings and metadata for a subset of COLD Cases (https://huggingface.co/datasets/harvard-lil/cold-cases).

    See: options in .env.example
    """
    environ = os.environ

    normalize_embeddings = environ["VECTOR_SEARCH_NORMALIZE_EMBEDDINGS"] == "true"
    chunk_prefix = environ["VECTOR_SEARCH_CHUNK_PREFIX"]

    pass

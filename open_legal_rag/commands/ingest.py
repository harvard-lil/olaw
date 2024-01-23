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
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from flask import current_app

from open_legal_rag import COLD_CASES_RECORD_DATA


@current_app.cli.command("ingest")
@click.option(
    "--court-jurisdiction",
    default=None,
    help="If set, will be used to filter cases by `court_jurisdiction`. Exact match. See https://huggingface.co/datasets/harvard-lil/cold-cases for details.",
)
@click.option(
    "--court-type",
    default=None,
    help="If set, will be used to filter cases by `court_type`. Exact match. See https://huggingface.co/datasets/harvard-lil/cold-cases for details.",
)
@click.option(
    "--year-min",
    default=None,
    help="If set, will be used to filter cases by `date_filled`.",
)
@click.option(
    "--year-max",
    default=None,
    help="If set, will be used to filter cases by `date_filled`.",
)
@click.option(
    "--limit",
    default=0,
    help="If set and > 0, only processes up to X entries from COLD Cases dataset.",
)
def ingest(court_jurisdiction=None, court_type=None, year_min=None, year_max=None, limit=0) -> None:
    """
    Generates embeddings and metadata for a subset of COLD Cases.

    COLD Cases: https://huggingface.co/datasets/harvard-lil/cold-cases

    See: options in .env.example
    """
    environ = os.environ

    normalize_embeddings = environ["VECTOR_SEARCH_NORMALIZE_EMBEDDINGS"] == "true"
    chunk_prefix = environ["VECTOR_SEARCH_CHUNK_PREFIX"]

    embedding_model = None
    text_splitter = None
    chroma_client = None
    chroma_collection = None
    cold_dataset = None

    # Filter input params
    if court_jurisdiction is not None:
        court_jurisdiction = str(court_jurisdiction)

    if court_type is not None:
        court_type = str(court_type)

    if year_min is not None:
        year_min = int(year_min)

    if year_max is not None:
        year_max = int(year_max)

    if year_min and year_max:
        try:
            assert year_min < year_max
        except Exception:
            click.echo("year_min must be inferior to year_max")
            exit(1)

    limit = int(limit)

    # Cleanup
    rmtree(environ["VECTOR_SEARCH_PATH"], ignore_errors=True)
    os.makedirs(environ["VECTOR_SEARCH_PATH"], exist_ok=True)

    # Init embedding model
    embedding_model = SentenceTransformer(
        environ["VECTOR_SEARCH_SENTENCE_TRANSFORMER_MODEL"],
        device=environ["VECTOR_SEARCH_SENTENCE_TRANSFORMER_DEVICE"],
    )

    # Init text splitter function
    text_splitter = SentenceTransformersTokenTextSplitter(
        model_name=environ["VECTOR_SEARCH_SENTENCE_TRANSFORMER_MODEL"],
        chunk_overlap=int(environ["VECTOR_SEARCH_TEXT_SPLITTER_CHUNK_OVERLAP"]),
        tokens_per_chunk=embedding_model[0].max_seq_length,
    )  # Note: The text splitter adjusts its cut-off based on the models' max_seq_length

    # Init vector store
    chroma_client = chromadb.PersistentClient(
        path=environ["VECTOR_SEARCH_PATH"],
        settings=chromadb.Settings(anonymized_telemetry=False),
    )

    chroma_collection = chroma_client.create_collection(
        name=environ["VECTOR_SEARCH_COLLECTION_NAME"],
        metadata={"hnsw:space": environ["VECTOR_SEARCH_DISTANCE_FUNCTION"]},
    )

    # Loading COLD Cases
    click.echo(f"Loading COLD Cases")
    cold_dataset = load_dataset("harvard-lil/cold-cases", split="train")

    for entry in cold_dataset:
        pass

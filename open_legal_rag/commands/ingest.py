"""
`commands.ingest` module: Controller for the `ingest` CLI command.
"""
import os
import traceback
import datetime
from shutil import rmtree

import click
import chromadb
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from flask import current_app

from open_legal_rag import COLD_CASES_OPINION_DATA, COLD_CASES_JURISDICTION_CODES


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

    cases_ingested = 0
    opinions_ingested = 0
    embeddings_stored = 0

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

    # Load COLD Cases
    click.echo("Loading COLD Cases")
    cold_dataset = load_dataset("harvard-lil/cold-cases", split="train")

    click.echo(f"📚 {len(cold_dataset)} cases found")

    # Generate embeddings for opinions and store them in vector store
    for i, case in enumerate(cold_dataset):
        click.echo(f"🔍 Case #{case['id']}")

        # Limit filter
        if limit > 0 and i > limit:
            click.echo(f"--limit ({limit}) reached. Interrupting.")
            break

        # Court jurisdiction filter
        if court_jurisdiction and case["court_jurisdiction"] != court_jurisdiction:
            click.echo(
                f"#{case['id']} --court-jurisdiction does not match filter ({case['court_jurisdiction']} != {court_jurisdiction}) - Skipping."  # noqa
            )
            continue

        # Court type filter
        if court_type and case["court_type"] != court_type:
            click.echo(
                f"#{case['id']} --court-type does not match filter ({case['court_type']} != {court_type}) - Skipping."  # noqa
            )
            continue

        # Year filter
        if (year_min or year_max) and not isinstance(case["date_filed"], datetime.date):
            click.echo(f"#{case['id']} has no date_filed: cannot check --year_min/max - Skipping.")
            continue

        if year_min and case["date_filed"].year < year_min:
            click.echo(f"#{case['date_filed']} before year_min {year_min} - Skipping.")
            continue

        if year_max and case["date_filed"].year > year_max:
            click.echo(f"#{case['date_filed']} after year_max {year_max} - Skipping.")
            continue

        # For each opinion:
        # - Split text using model-appropriate text-splitter
        # - Generate embeddings for resulting chunks
        # - Store resulting embeddings + meta data in vector store
        for opinion in case["opinions"]:
            case_plus_opinion_id = f"- Opinion #{opinion['opinion_id']} for case #{case['id']}"

            if not opinion["opinion_text"] or not opinion["opinion_text"].strip():
                click.echo(f"{case_plus_opinion_id} has no text - Skipping.")
                continue

            # Split chunks
            text_chunks = text_splitter.split_text(opinion["opinion_text"])
            click.echo(f"{case_plus_opinion_id} -> {len(text_chunks)} chunks.")

            if not text_chunks:
                continue

            # Add VECTOR_SEARCH_CHUNK_PREFIX to every chunk
            for i in range(0, len(text_chunks)):
                text_chunks[i] = chunk_prefix + text_chunks[i]

            # Generate embeddings and metadata for each chunk
            documents = []
            metadatas = []
            ids = []

            embeddings = embedding_model.encode(
                text_chunks,
                normalize_embeddings=normalize_embeddings,
            )

            for i, text_chunk in enumerate(text_chunks):
                documents.append(str(case["id"]))
                ids.append(f"{case['id']}-{opinion['opinion_id']}-{i}")

                metadata = dict(COLD_CASES_OPINION_DATA)
                metadata["case_id"] = case["id"]

                if case["date_filed"]:
                    metadata["case_date_filed"] = str(case["date_filed"])

                if case["case_name"]:
                    metadata["case_name"] = case["case_name"]

                if case["judges"]:
                    metadata["case_judges"] = case["judges"]

                if case["attorneys"]:
                    metadata["case_attorneys"] = case["attorneys"]

                if case["court_full_name"]:
                    metadata["court_name"] = case["court_full_name"]

                metadata["opinion_id"] = opinion["opinion_id"]

                if opinion["author_str"]:
                    metadata["opinion_author"] = opinion["author_str"]

                metadata["opinion_text"] = text_chunk[len(chunk_prefix) :]  # noqa

                metadatas.append(metadata)

            embeddings = embeddings.tolist()

            # Store embeddings and metadata
            chroma_collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

            opinions_ingested += 1
            embeddings_stored += len(embeddings)

        cases_ingested += 1

    # Summary
    click.echo(80 * "-")
    click.echo(f"{cases_ingested} cases ingested.")
    click.echo(f"{opinions_ingested} opinions ingested.")
    click.echo(f"{embeddings_stored} embeddings stored.")

import os
import re
import traceback
import requests
import html2text

from . import SearchTarget


class CourtListener(SearchTarget):

    RESULTS_DATA_FORMAT = {
        "id": "",
        "case_name": "",
        "court": "",
        "absolute_url": "",
        "status": "",
        "date_filed": "",
        "text": "",  # Full opinion text
        "prompt_text": "",  # Line of text used as part of the RAG prompt to introduce sources.
        "ui_text": "",  # Line of text used as part of the UI to introduce this source.
        "ui_url": "",  # URL used to let users explore this source.
    }
    """
    Shape of the data for each individual entry of search_results.
    """

    @staticmethod
    def search(search_statement: str):
        """
        Runs search_statement against the CourtListener search API.
        - Returns up to COURT_LISTENER_MAX_RESULTS results.
        - Objects in list use the CourtListener.RESULTS_DATA_FORMAT template.
        """
        api_url = os.environ["COURT_LISTENER_API_URL"]
        base_url = os.environ["COURT_LISTENER_BASE_URL"]
        max_results = int(os.environ["COURT_LISTENER_MAX_RESULTS"])

        raw_results = None
        prepared_results = []

        filed_before = None
        filed_after = None

        # Extract date range from "search_statement":
        # This is to account for dateFiled:[X TO Y] working inconsistently
        if "dateFiled" in search_statement:
            pattern_filed_after = r"dateFiled\:\[([0-9]{4}-[0-9]{2}-[0-9]{2}) TO"

            pattern_filed_before = (
                r"dateFiled\:\[[0-9]{4}-[0-9]{2}-[0-9]{2} TO ([0-9]{4}-[0-9]{2}-[0-9]{2})\]"
            )
            try:
                filed_after = re.findall(pattern_filed_after, search_statement)[0]
                filed_after = filed_after.replace("-", "/")

                filed_before = re.findall(pattern_filed_before, search_statement)[0]
                filed_before = filed_before.replace("-", "/")
            except Exception:
                pass

        print(filed_after)
        print(filed_before)

        #
        # Pull search results
        #
        raw_results = requests.get(
            f"{api_url}search/",
            timeout=10,
            params={
                "type": "o",
                "order": "score desc",
                "q": search_statement,
                "filed_after": filed_after,
                "filed_before": filed_before,
            },
        ).json()

        #
        # Pull opinion text for the first X results
        #
        for i in range(0, max_results):
            if i > len(raw_results["results"]) - 1:
                break

            opinion = dict(CourtListener.RESULTS_DATA_FORMAT)

            opinion_metadata = raw_results["results"][i]

            # Case-specific data
            opinion["id"] = opinion_metadata["id"]
            opinion["case_name"] = opinion_metadata["caseName"]
            opinion["court"] = opinion_metadata["court"]
            opinion["absolute_url"] = base_url + opinion_metadata["absolute_url"]
            opinion["status"] = opinion_metadata["status"]
            opinion["date_filed"] = opinion_metadata["dateFiled"]

            # Request and format opinion text
            try:
                opinion_data = requests.get(
                    f"{api_url}opinions/",
                    timeout=10,
                    params={"id": opinion["id"]},
                ).json()

                opinion_data = opinion_data["results"][0]
                opinion["text"] = html2text.html2text(opinion_data["html"])

            except Exception:
                continue

            # Text for LLM (context intro)
            # [1] Foo v. Bar (1996) Court Name, as sourced from http://url:
            opinion["prompt_text"] = f"[{i+1}] "  # [1]
            opinion["prompt_text"] += f"{opinion['case_name']} "  # Foo v. Bar
            opinion["prompt_text"] += f"({opinion['date_filed'][0:4]}) "  # (1996)
            opinion["prompt_text"] += f"{opinion['court']}, "  # US Supreme Court
            opinion["prompt_text"] += f"as sourced from {opinion['absolute_url']}:"

            # Text for UI
            # [1] Foo v. Bar (1996), Court Name
            opinion["ui_text"] = f"[{i+1}] "  # [1]
            opinion["ui_text"] += f"{opinion['case_name']} "  # Foo v. Bar
            opinion["ui_text"] += f"({opinion['date_filed'][0:4]}), "  # (1996)
            opinion["ui_text"] += f"{opinion['court']} "  # US Supreme Court
            opinion["ui_url"] = opinion["absolute_url"]

            prepared_results.append(opinion)

        return prepared_results

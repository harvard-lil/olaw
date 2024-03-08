# Open Legal AI Workbench (OLAW)

**AI + Legal APIs**: A Tool-Based Retrieval Augmented Generation Workbench for Legal AI UX Research. 

More info:
- <a href="https://lil.law.harvard.edu/2024/03/08/announcing-the-open-legal-ai-workbench-olaw/">"Cracking the justice barrier: announcing the Open Legal AI Workbench"</a>. Mar 08 2024 - _lil.law.harvard.edu_

https://github.com/harvard-lil/olaw/assets/625889/65dd61db-42f8-490b-a737-0612d97c5c81

> **Video**: OLAW’s chatbot retrieving court opinions from the CourtListener API to help answer a legal question. 
> Information is interpreted by the AI model, which may make mistakes.

---

## Summary
- [Concept](#concept)
- [Installation](#installation)
- [Configuring the application](#configuring-the-application)
- [Starting the server](#starting-the-server)
- [Recommended models](#recommended-models)
- [Interacting with the Web UI](#interacting-with-the-web-ui)
- [Interacting with the API](#interacting-with-the-api)
- [Adding new tools](#adding-new-tools)
- [Getting Involved](#getting-involved)
- [Cite this repository](#cite-this-repository)
- [Disclaimer](#disclaimer)

---

## Concept

**OLAW** is a tool-based [Retrieval Augmented Generation](https://www.promptingguide.ai/techniques/rag) (RAG) workbench for legal AI UX research. 
It consists of a customizable chatbot that can use legal APIs to augment its responses.

**The goal of this project is to simplify and streamline experimentation with APIs-based RAG in legal contexts by:**
- **Keeping it simple**: The tool should be easy to operate, modify and interpret.
- **Being highly customizable and modular**: [Adding a tool](#adding-new-tools) to this workbench should be as simple as possible.
- **Being open and collaborative**: A lot of this work generally happens behind the scenes. This project aims at amplifying collaborative research on the uses of AI in legal contexts.

The focus here is on ease of access and experimentation, as opposed to overall performance or production-readiness. 

### Tool-based RAG?
There are as many "flavors" of RAG as there are implementations of it. 
This workbench focuses on a tool-based approach, in which **the LLM is indirectly given access to APIs** as a way to augment its responses. 

**This process takes place in three steps:**
1. _Upon receiving a message from the user, the pipeline asks the LLM to analyze the message to:_
    - Detect if it contains a legal question
    - [Use a prompt](/.env.example#L37) to determine where to look for additional information _(search target)_
    - Use that same prompt to generate a search statement to use against the search target 
2. _Upon identifying a search suggestion._
    - The UI presents the search suggestion to the user and ask for confirmation.
3. _Upon confirmation from the user:_
    - The pipeline performs the suggested search against the search target ... 
    - ... and uses the results as additional context when asking the LLM to answer the user's question

[☝️ Summary](#summary)

---

## Installation

OLAW requires the following machine-level dependencies to be installed. 

- [Python 3.11+](https://python.org)
- [Python Poetry](https://python-poetry.org/)

Use the following commands to clone the project and instal its dependencies:

```bash
# MacOS / Linux / WSL
git clone https://github.com/harvard-lil/olaw.git
cd olaw
poetry install
```

The workbench itself doesn't have specific hardware requirements. If you would like to use [Ollama](https://ollama.ai) for local inference with open-source language models, be sure to check their [system requirements](https://github.com/ollama/ollama?tab=readme-ov-file#model-library).

[☝️ Summary](#summary)

---

## Configuring the application 

This program uses environment variables to handle settings. 
Copy `.env.example` into a new `.env` file and edit it as needed.

```bash
cp .env.example .env
```

See details for individual settings in [.env.example](.env.example).

**A few notes:**
- OLAW can interact with both the [Open AI API](https://platform.openai.com/docs/introduction) and [Ollama](https://ollama.ai) for local inference. 
  - Both can be used at the same time, but at least one is needed. 
  - By default, the program will try to communicate with Ollama's API at `http://localhost:11434`.
  - It is also possible to use OpenAI's client to interact with compatible providers, such as [HuggingFace's Message API](https://huggingface.co/blog/tgi-messages-api) or [vLLM](https://docs.vllm.ai/en/latest/getting_started/quickstart.html#using-openai-completions-api-with-vllm). To do so, set values for both `OPENAI_BASE_URL` and `OPENAI_COMPATIBLE_MODEL` environment variables. 
- Prompts can be edited directly in the configuration file.

[☝️ Summary](#summary)

---

## Starting the server

The following command will start the OLAW (development) server on port `5000`.

```bash
poetry run flask run
# Not: Use --port to use a different port
```

[☝️ Summary](#summary)

---

## Recommended models

While this pipeline can in theory be run against a wide variety of text generation models, there are two key constraints to keep in mind when picking an LLM:
- The size of the **context window**. The target model needs to be able to handle long input, as the pipeline may pull additional context from APIs it has access to.
- Ability to **reliably return JSON data**. This feature is used by the `/api/extract-search-statement` route.

**We have tested this software with the following models:**
- OpenAI: `openai/gpt-4-turbo-preview` _(128K tokens context)_
- Ollama: Any version of `ollama/mixtral`_(32K tokens context + sliding window)_

We have observed performance with `openai/gpt-4-turbo-preview` during out initial tests, using the default prompts.

[☝️ Summary](#summary)

---

## Interacting with the WEB UI

Once the server is started, the application's web UI should be available at `http://localhost:5000`.

The interface automatically handles a basic chat history, allowing for few-shots / chain-of-thoughts prompting. 

[☝️ Summary](#summary)

---

## Interacting with the API

OLAW comes with a REST API that can be used to interact programmatically with the workbench. 

> New to REST APIs? See this [tutorial](https://www.smashingmagazine.com/2018/01/understanding-using-rest-api/).

### [GET] /api/models
Returns a list of available models as JSON.

<details>
<summary><strong>Sample output</strong></summary>

```json
[
    "openai/gpt-4-vision-preview",
    "openai/gpt-4-0613",
    "openai/gpt-4-0125-preview",
    "openai/gpt-4-turbo-preview",
    "openai/gpt-4",
    "openai/gpt-4-1106-preview",
    "ollama/llama2:13b",
    "ollama/llama2:13b-chat-fp16",
    "ollama/llama2:70b",
    "ollama/llama2:70b-chat-fp16",
    "ollama/llama2:7b",
    "ollama/llama2:latest",
    "ollama/mistral:7b",
    "ollama/mistral:7b-instruct-fp16",
    "ollama/mistral:7b-instruct-v0.2-fp16",
    "ollama/mixtral:8x7b-instruct-v0.1-fp16",
    "ollama/mixtral:8x7b-instruct-v0.1-q6_K",
    "ollama/mixtral:latest",
    "ollama/phi:2.7b-chat-v2-fp16"
]
```

</details>

### [POST] /api/extract-search-statement
Uses the [search statement extraction prompt](/olaw/blob/main/.env.example#L37) to:
- Detect if the user asked a question that requires pulling information from a legal database
- If so, transform said question into a search statement that can be run against a known search target (See [`SEARCH_TARGETS`](/olaw/const/__init__.py)).


Returns a JSON object containing `search_statement` and `search_target`. These properties can be empty.

<details>
<summary><strong>Sample input</strong></summary>

```json
{
    "model": "ollama/mixtral",
    "temperature": 0.0,
    "message": "Tell me everything you know about Miranda v. Arizona (1966)"
}
```

**Notes:**
- `temperature` is optional.

</details>

<details>
<summary><strong>Sample output</strong></summary>


```json
{
    "search_statement": "caseName:(\"Miranda v. Arizona\") AND dateFiled:[1966-01-01 TO 1966-12-31]",
    "search_target": "courtlistener"
}
```

</details>


### [POST] /api/search
Performs search using what `/api/extract-search-statement` returned.

Returns a JSON object with search results indexed by `SEARCH_TARGET`.

<details>
<summary><strong>Sample input</strong></summary>

```json
{
    "search_statement": "caseName:(\"Miranda v. Arizona\") AND dateFiled:[1966-01-01 TO 1966-12-31]",
    "search_target": "courtlistener"
}
```

</details>

<details>
<summary><strong>Sample output</strong></summary>

```json
{
    "courtlistener": [
        {
            "absolute_url": "https://www.courtlistener.com/opinion/107252/miranda-v-arizona/",
            "case_name": "Miranda v. Arizona",
            "court": "Supreme Court of the United States",
            "date_filed": "1966-06-13T00:00:00-07:00",
            "id": 107252,
            "ref_tag": 1,
            "status": "Precedential",
            "text": "..."
        },
        {
            "absolute_url": "https://www.courtlistener.com/opinion/8976604/miranda-v-arizona/",
            "case_name": "Miranda v. Arizona",
            "court": "Supreme Court of the United States",
            "date_filed": "1969-10-13T00:00:00-07:00",
            "id": 8968349,
            "ref_tag": 2,
            "status": "Precedential",
            "text": "..."
        },
        {
            "absolute_url": "https://www.courtlistener.com/opinion/8962758/miranda-v-arizona/",
            "case_name": "Miranda v. Arizona",
            "court": "Supreme Court of the United States",
            "date_filed": "1965-11-22T00:00:00-08:00",
            "id": 8953989,
            "ref_tag": 3,
            "status": "Precedential",
            "text": "..."
        }
    ]
}
```

</details>

### [POST] /api/complete
Passes messages and context to target LLM and starts **streaming** text completion. Returns raw text, streamed.

<details>
<summary><strong>Sample input</strong></summary>

```json
{
    "message": "Tell me everything you know about Miranda v. Arizona (1966)",
    "model": "openai/gpt-4-turbo-preview",
    "temperature": 0.0,
    "max_tokens": 4000,
    "search_results": {
        "courtlistener": [...]
    },
    "history": [
        {"role": "user", "content": "Hi there!"},
        {"role": "assistant", "content": "How may I help you?"}
    ]
}
```

**Notes:**
- `temperature` is optional.
- `max_tokens` is optional.
- `history` must be an array of objects containing `role` and `content` keys. `role` can be either `user` or `assistant`.

</details>

[☝️ Summary](#summary)

---

## Adding new tools

This section of the documentation describes the process of making OLAW understand and use additional _"search target"_ beyond the Court Listener API.

<details>
<summary><strong>1. Declare a new search target</strong></summary>

Edit the [`SEARCH_TARGETS`](/olaw/search_targets/__init__.py) list under [`olaw/search_results/__init__.py`](/olaw/search_targets/__init__.py) to declare a new search target. 

Lets call this new target `casedotlaw`.

```python
SEARCH_TARGETS = ["courtlistener", "casedotlaw"]
```

</details>

<details>
<summary><strong>2. Edit search statement extraction prompt</strong></summary>

Edit `EXTRACT_SEARCH_STATEMENT_PROMPT` in your `.env` file to let the LLM know how to write search statements for this new tool.

This prompt is used by `/api/extract-search-statement`, which is then able to output objects as follows:

```json
{
    "search_statement": "(Platform-specific search statement based on user question)",
    "search_target": "casedotlaw"
}
```

The process of designing a performant prompt for that task generally requires a few iterations.

</details>

<details>
<summary><strong>3. Add handling logic</strong></summary>

Add a file under the `olaw/search_targets/` folder, named after your search target. In that case: `casedotlaw.py`.

This file must contain a class inheriting from `SearchTarget`, which defines 1 property and 1 static method:
- `RESULTS_DATA_FORMAT` determining how search results data is structured
- `search()` containing logic for returning search results

You may refer to [`courtlistener.py` as an example](/olaw/search_targets/courtlistener.py).

You will also need to edit [`olaw/search_results/__init__.py`](/olaw/search_targets/__init__.py) as follows:
- Import `casedotlaw.py`
- Edit `route_search()` to account for that new target

</details>

[☝️ Summary](#summary)

---

## Getting Involved

This project is collaborative at its core and we warmly welcome feedback and contributions.

- [The issues tab](/issues) is a good place to start to report bugs, suggest features or volunteer to contribute to the codebase on a specific issue.
- Don't hesitate to use [the discussions tab](/discussions) to ask more general questions about this project.


[☝️ Summary](#summary)

---

## Cite this repository 

> Cargnelutti, M., & Cushman, J. (2024). Open Legal AI Workbench (OLAW) (Version 0.0.1) [Computer software]

See also: 
- [Our citation file](https://github.com/harvard-lil/olaw/blob/main/CITATION.cff)
- The _"Cite this repository"_ button in the About section of this repository. 

[☝️ Summary](#summary)

---

## Disclaimer

The Library Innovation Lab is an organization based at the Harvard Law School Library. We are a cross-functional group of software developers, librarians, lawyers, and researchers doing work at the edges of technology and digital information.

Our work is rooted in library principles including longevity, authenticity, reliability, and privacy. Any work that we produce takes these principles as a primary lens. However due to the nature of exploration and a desire to prototype our work with real users, we do not guarantee service or performance at the level of a production-grade software for all of our releases. This includes this project, which is an experimental boilerplate released under [MIT License](LICENSE).

Open Legal AI Workbench is an experimental tool for evaluating legal retrieval software and should not be used for legal advice.

[☝️ Summary](#summary)

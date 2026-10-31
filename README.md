# Empório da Música — AI Customer Support Agent

A command-line customer-support assistant for Empório da Música. It answers in Brazilian Portuguese and uses local product/order data and the store-policy PDF to ground its responses.

## Requirements

- Python 3.9 or newer
- A Groq API key
- The project data files in the `data/` directory

## Setup

From the project root, create and activate a virtual environment, then install the dependencies.

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create a `.env` file in the project root by copying `.env.example`.

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**macOS/Linux**

```bash
cp .env.example .env
```

Then replace the placeholder with your Groq API key:

```text
GROQ_API_KEY=your_groq_api_key
```

Keep the key private and do not commit `.env`. The application loads it from the project root.

## Run

Start the interactive assistant from the project root:

```powershell
python main.py
```

Enter a customer question. Type `exit` or `quit` to end the session. Conversation history is kept in memory for that CLI session only.

To run one randomly selected query for each of the three example scenarios and write the answers to `final_results.csv`:

```powershell
python run_scenarios.py
```

This script makes live requests to Groq and overwrites `final_results.csv`. It requires a working API key and network access.

## Provider and model

The project calls the **Groq API** using the official `groq` Python SDK and its chat-completions interface. The configured model identifier is `openai/gpt-oss-20b`; this is the model name served through Groq, not a request to the OpenAI API. The API key is configured with `GROQ_API_KEY` in `.env`.

## Architecture and technical decisions

The implementation is a small Python CLI application rather than a web framework: the requested interaction is a local, single-user terminal workflow, so a web server or heavier agent framework would add setup and runtime complexity without helping the current use case.

The request flow is:

1. `main.py` reads user input and keeps the conversation history in memory.
2. `src/agent.py` sends the system prompt and conversation to Groq, with three function tools available. It executes requested tools and returns the model's answer.
3. `src/tools.py` exposes product search, order lookup, and policy search to the model.
4. `src/database.py` uses pandas to load the local CSV files under `data/` and look up products and orders.
5. `src/rag.py` extracts text from `data/políticas_da_loja.pdf`, normalizes whitespace, splits it at numbered subsections, and breaks unusually long sections into bounded chunks. It ranks chunks by matching query terms and returns the matching policy text to the model as tool output.

This policy retrieval is a lightweight lexical retrieval approach, not embedding-based or vector-database RAG. It avoids extra infrastructure and dependencies for the small, local policy document. The other tools query the CSVs directly so exact product and order facts come from the supplied data instead of model memory.

The system prompt sets the assistant's language and tone, limits the store's scope to musical instruments, directs the model to use tools for factual product/order/policy answers, and tells it not to invent facts. The agent uses automatic tool selection, disables parallel tool calls, and uses a low temperature. It also removes `**` markers from the returned answer to avoid unwanted Markdown bold formatting.

### Project files

- `main.py` — interactive CLI entry point.
- `run_scenarios.py` — runs sample queries and writes `final_results.csv`.
- `src/config.py` — project paths, environment loading, API key, and model name.
- `src/agent.py` — prompt, tool definitions, Groq calls, and response cleanup.
- `src/tools.py` — functions exposed to the model.
- `src/database.py` — CSV-backed product and order operations.
- `src/rag.py` — PDF text extraction and lexical policy retrieval.
- `data/` — CSV datasets and the store policy PDF.
- `examples/` — four example conversations: product search, return-policy application, product pricing, and store address lookup.

## Known limitations and next steps

- Policy retrieval uses simple word matching. It can miss relevant passages when a question uses different wording, and it does not understand semantic similarity. With more time, I would evaluate a Portuguese-capable embedding model and vector retrieval against representative questions, while retaining source passages for grounded answers.
- PDF text extraction and numbered-section detection are intentionally simple. Scanned PDFs, unusual formatting, or policies without numbered headings may not be segmented well. I would add ingestion checks, configurable chunking, and tests for more policy documents.
- If the policy PDF is missing, the current loader leaves the policy chunks empty; the app does not fail at startup. I would make this condition visible and add a clear setup/health check.
- CSV files are loaded into memory when the tool module is imported. This is appropriate for the included static sample data, but it does not support concurrent updates or larger production datasets. I would move changing operational data to a database and add explicit schema/data validation.
- The model and API are external dependencies. Responses can vary, requests need network access, and API availability, latency, and cost are outside the application's control. I would add timeouts, structured logs, retry rules for transient failures, and request/cost monitoring.
- The scenario runner randomly selects one query per scenario, so outputs are not fully reproducible and are not an automated quality test. I would add deterministic evaluation cases, expected tool-call checks, and automated tests using mocked API responses.
- The CLI is intended as a local demo. It does not provide user authentication, authorization, persistent sessions, or production privacy controls. I would design those before exposing it as a customer-facing service.

## Use of coding assistants

GitHub Copilot in VS Code (using the Copilot SDK) was used as a coding assistant during development. It helped inspect the project structure, organize the notebook-based implementation into regular Python modules and scripts, improve the README, and make targeted code changes. Changes were checked against the existing source and validated with Python compilation and focused local smoke checks. The assistant was used to support implementation and documentation; project behavior and factual responses still depend on the code, supplied data, and Groq model/API.

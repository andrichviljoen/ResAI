# ActuaryGPT Triangle Diagnostic Workbench

Production-oriented Streamlit app for actuarial triangle diagnostics, reserving review, and AI commentary grounded on deterministic outputs.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Set `OPENAI_API_KEY` for live AI responses; otherwise deterministic fallback commentary is used.

## Test

```bash
pytest -q
```

## Architecture

- `app.py`: Streamlit entrypoint.
- `actuarygpt_workbench/pages/main_workspace.py`: seven-section professional workspace.
- `actuarygpt_workbench/services/*`: ingestion, triangle, samples, export.
- `actuarygpt_workbench/actuarial/*`: diagnostics + reserving engines.
- `actuarygpt_workbench/ai/copilot.py`: structured AI service and prompt templates.
- `tests/*`: parsing, triangles, diagnostics, exports, sample model smoke.

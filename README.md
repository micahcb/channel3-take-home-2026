## Channel3 Take Home Assignment

1. Running the data extraction
   - uv sync
   - uv run main.py
2. Running the api 
   - uv sync
   - uv run api.py
3. Running the frontend
   - npm install 
   - npm run dev

4. Model testing (cost and speed)
   - Variable: which LLM model is used.
   - Output per run: time (seconds), cost (USD), error (if any), product (extracted JSON).
   - Run: `uv run python -m scripts.run_model_test [--html data/ace.html] [--out scripts/model_test_results.json] [--models "openai/gpt-5-nano,openai/gpt-5-mini"]`
   - Results are written to a JSON file (default: `scripts/model_test_results.json`).


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

4. Model testing infrastructure for cost and speed
   - Variable: which LLM model is used.
   - Output per run: time (seconds), cost (USD), error (if any), product (extracted JSON).
   - Run: `uv run python -m scripts.run_model_test [--html data/ace.html] [--out scripts/model_test_results.json] [--models "openai/gpt-5-nano,openai/gpt-5-mini"]`
   - Results are written to a JSON file (default: `scripts/model_test_results.json`).



Provide a brief (1-2 paragraph) write-up of how you would turn the system you’ve built into a web-scale operation. For the backend, how would you scale this system up from 5 products to 50 million? What assumptions have you made here that will scale, and what assumptions won’t scale? For the frontend, what API would you provide to power agentic shopping apps? What other tools can you provide developers to help power new shopping experiences?

---

## System Design: Scaling to Web-Scale

**Backend (5 → 50M products), with focus on search and LLM cost**

Today I built the simple backend that runs in around a minute and half for approximately $.01. The only "search" is exact character search on the frontend. That does not scale. I see search as the main functionality selling point for users and LLM cost as the glaring main cost, so to scale those two painpoints is goal #1 (aside from the obvious storage infrastructure that needs to be built). To reach 50M products I'd first focus on data ingestion. I would move to a proper data layer like PostgreSQL and or ingestion at scale we'd run extraction in an async redis job queue with a frontier link list that would either be completely handled internally through classic webscraping logic, or allow user link input which would simply add to the queue. For the LLM cost I built a LangChain graph with simple testing infrastructure. Assuming that time is not an issue as these jobs run on an async queue cost is our main concern. Through my testing the cheapest model that met quality was gpt-5-nano. Assuming 10 million pages this costs around $130,000 for one iteration. So to limit cost I would focus on the input cost of choosing the category. Currently we include the entire .txt file with the categories, but not only is this huge, it can grow. To start I would test the cost tradeoffs of using a two step process where we break the category choice into first choose a broad category, and then choosing a leaf node only from the subset of the text that has the previously chosen base category. This would cut down the cost into one call that only the 21 total base categories instead of the entire categories.txt input tokens, and then a second that maximum around 1/5 of the total current input tokens (Biggest vategory is Home & Garden with 1,035). Because the flow is built is a langgraph it allows for rapid, simple iteration on testing. Specifically we could test this different flow without worrying about constantly rebuilding state management.
I would then focus on a dedicated search stack: Elasticsearch/OpenSearch for full-text and/or semantic search, with bulk indexing and pagination so the API never loads the full catalog. Additionally to scale search I would (1) indexing product fields (name, brand, category, description) at write time, (2) serve queries via the search engine instead of scanning a list (3) optionally hybrid search (keyword + embeddings) for agent-style "find me X" queries. 

Assumptions that scale: structured extraction (category → product) and cost caps per run. Assumptions that don't: reading the whole catalog on every request, running LLM inline per request, and having no search index.

**Frontend: API for agentic shopping and developer tools**

# 💬 codechat: Chat with your codebase

Ask natural-language questions about any repository and get answers grounded in the actual code, with `file:line` citations.

```
you> how are python files split into chunks?
claude> Python files are parsed with `ast` and split at top-level functions and
classes (`codechat/ingest.py:61-83`). Large classes fall back to fixed
60-line windows with 10 lines of overlap ...
```

## How it works (RAG)

```
repo ──► ingest ──► chunks ──► embeddings ──► index (.npy + .json)
                                                 │
question ──► embed ──► top-k similar chunks ◄────┘
                              │
                              ▼
                     Claude (question + excerpts) ──► answer with citations
```

1. **Ingest**: walk the repo, skip `node_modules`, `.git`, binaries and huge files.
2. **Chunk**: Python is split by function/class using `ast`; other files use overlapping line windows.
3. **Embed**: a local `sentence-transformers` model (free, no API key needed).
4. **Retrieve**: cosine similarity plus a small keyword boost for exact identifiers.
5. **Generate**: Claude answers using only the retrieved excerpts.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```bash
python -m codechat.cli index https://github.com/pallets/flask   # or a local path
python -m codechat.cli ask "Where is routing implemented?"
python -m codechat.cli chat                                      # interactive mode
```

Optional environment variables: `CODECHAT_MODEL`, `CODECHAT_EMBED_MODEL`, `CODECHAT_INDEX_DIR`.

## Roadmap ideas

- [ ] Tree-sitter chunking for JS/TS/Go/Java
- [ ] Incremental re-indexing (hash files, embed only changed ones)
- [ ] Vector DB backend (Chroma / Qdrant) for large repos
- [ ] Hybrid search with BM25 + reranker
- [ ] Web UI (Streamlit or FastAPI + React)
- [ ] GitHub Action that answers questions in issues
- [ ] Eval set: question → expected file, measure retrieval hit-rate

## License
MIT

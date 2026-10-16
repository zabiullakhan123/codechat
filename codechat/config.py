import os

# LLM
LLM_MODEL = os.getenv("CODECHAT_MODEL", "claude-sonnet-5-5")
MAX_TOKENS = int(os.getenv("CODECHAT_MAX_TOKENS", "1500"))

# Embeddings (runs locally, no API key needed)
EMBED_MODEL = os.getenv("CODECHAT_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Chunking
CHUNK_LINES = 60          # lines per chunk
CHUNK_OVERLAP = 10        # lines shared between neighbouring chunks
MAX_FILE_BYTES = 500_000  # skip huge/generated files

# Retrieval
TOP_K = 8

INDEX_DIR = os.getenv("CODECHAT_INDEX_DIR", ".codechat_index")

CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".go", ".rs", ".rb",
    ".php", ".c", ".h", ".cpp", ".hpp", ".cs", ".swift", ".scala", ".sh",
    ".sql", ".html", ".css", ".scss", ".vue", ".svelte",
    ".md", ".rst", ".txt", ".yaml", ".yml", ".toml", ".json", ".ini", ".cfg",
}
SPECIAL_FILES = {"Dockerfile", "Makefile", "README", "LICENSE"}
IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", "__pycache__", "dist",
    "build", ".next", "target", ".idea", ".vscode", "vendor", ".codechat_index",
}

"""Load files from a local path or GitHub URL and split them into chunks."""
import ast
import os
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path

from . import config


@dataclass
class Chunk:
    path: str        # path relative to repo root
    start_line: int  # 1-based, inclusive
    end_line: int
    text: str

    def to_dict(self):
        return asdict(self)


def resolve_repo(source: str) -> Path:
    """Return a local path; clone first if `source` is a git URL."""
    if source.startswith(("http://", "https://", "git@")):
        from git import Repo
        dest = Path(tempfile.mkdtemp(prefix="codechat_"))
        print(f"Cloning {source} ...")
        Repo.clone_from(source, dest, depth=1)
        return dest
    path = Path(source).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Not a directory: {path}")
    return path


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in config.IGNORE_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in config.CODE_EXTENSIONS or p.stem in config.SPECIAL_FILES:
                try:
                    if p.stat().st_size <= config.MAX_FILE_BYTES:
                        yield p
                except OSError:
                    continue


def _line_chunks(rel, lines, offset=0):
    """Fixed-size line windows with overlap."""
    step = config.CHUNK_LINES - config.CHUNK_OVERLAP
    for start in range(0, max(len(lines), 1), step):
        window = lines[start:start + config.CHUNK_LINES]
        if not "".join(window).strip():
            continue
        yield Chunk(rel, offset + start + 1, offset + start + len(window), "".join(window))
        if start + config.CHUNK_LINES >= len(lines):
            break


def _python_chunks(rel, source, lines):
    """Split Python by top-level functions/classes so chunks are meaningful units."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        yield from _line_chunks(rel, lines)
        return
    covered_until = 0
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        start = (node.decorator_list[0].lineno if node.decorator_list else node.lineno) - 1
        end = node.end_lineno
        if start > covered_until:  # module-level code between definitions
            yield from _line_chunks(rel, lines[covered_until:start], covered_until)
        block = lines[start:end]
        if len(block) > config.CHUNK_LINES * 2:  # very large class -> split it
            yield from _line_chunks(rel, block, start)
        else:
            yield Chunk(rel, start + 1, end, "".join(block))
        covered_until = end
    if covered_until < len(lines):
        yield from _line_chunks(rel, lines[covered_until:], covered_until)


def chunk_repo(root: Path):
    chunks = []
    for p in iter_files(root):
        try:
            source = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(p.relative_to(root))
        lines = source.splitlines(keepends=True)
        if p.suffix == ".py":
            chunks.extend(_python_chunks(rel, source, lines))
        else:
            chunks.extend(_line_chunks(rel, lines))
    return chunks

"""CodeIndex: vector search (Chroma) + exact lookups over the chunk list."""
import json, re
from pathlib import Path
import chromadb
from ingest.chunker import chunk_repo
from .embed import get_embedder


class CodeIndex:
    def __init__(self, repo_path: str):
        self.repo = Path(repo_path).resolve()
        self.dir = self.repo / ".codeagent"
        self._chunks: list[dict] | None = None

    # ---------- build ----------
    def build(self) -> int:
        chunks = [c.to_dict() for c in chunk_repo(str(self.repo))]
        self.dir.mkdir(exist_ok=True)
        (self.dir / "chunks.json").write_text(json.dumps(chunks))
        client = chromadb.PersistentClient(path=str(self.dir / "chroma"))
        try:
            client.delete_collection("chunks")
        except Exception:
            pass
        col = client.create_collection("chunks", embedding_function=get_embedder(),
                                       metadata={"hnsw:space": "cosine"})
        for i in range(0, len(chunks), 200):
            batch = chunks[i:i + 200]
            col.add(
                ids=[c["id"] for c in batch],
                documents=[self._doc(c) for c in batch],
                metadatas=[{k: c[k] for k in ("file", "name", "kind", "parent",
                                              "start_line", "end_line")} for c in batch],
            )
        self._chunks = chunks
        return len(chunks)

    @staticmethod
    def _doc(c: dict) -> str:
        qual = f"{c['parent']}.{c['name']}" if c["parent"] else c["name"]
        return f"{c['kind']} {qual} in {c['file']}\n{c['code'][:4000]}"

    # ---------- load ----------
    @property
    def chunks(self) -> list[dict]:
        if self._chunks is None:
            p = self.dir / "chunks.json"
            if not p.exists():
                raise FileNotFoundError("No index found. Run: python cli.py index <repo>")
            self._chunks = json.loads(p.read_text())
        return self._chunks

    def _col(self):
        client = chromadb.PersistentClient(path=str(self.dir / "chroma"))
        return client.get_collection("chunks", embedding_function=get_embedder())

    # ---------- queries ----------
    def search(self, query: str, k: int = 6) -> list[dict]:
        res = self._col().query(query_texts=[query], n_results=k)
        by_id = {c["id"]: c for c in self.chunks}
        return [by_id[i] for i in res["ids"][0] if i in by_id]

    def get_symbol(self, name: str) -> list[dict]:
        """Accepts 'name', 'Class.method', or 'path/file.py:name'. Falls back to
        finding small helpers defined *inside* another function."""
        name = name.strip()
        file_hint = None
        if ":" in name:
            file_hint, name = name.rsplit(":", 1)
        name = name.strip().rstrip("()")
        res = [c for c in self.chunks
               if c["name"] == name or f"{c['parent']}.{c['name']}" == name]
        if file_hint:
            narrowed = [c for c in res if c["file"].endswith(file_hint.strip())]
            res = narrowed or res
        if not res:
            last = re.escape(name.split(".")[-1])
            pat = re.compile(rf"^\s*(?:async\s+)?(?:def|function|class|const|let|var)\s+{last}\b", re.M)
            res = [c for c in self.chunks if pat.search(c["code"])]
        return res[:5]

    def find_usages(self, name: str, limit: int = 15) -> list[dict]:
        pat = re.compile(rf"\b{re.escape(name)}\b")
        hits = [c for c in self.chunks if c["name"] != name and pat.search(c["code"])]
        return hits[:limit]


def format_chunk(c: dict, max_chars: int = 2500) -> str:
    qual = f"{c['parent']}.{c['name']}" if c["parent"] else c["name"]
    return (f"[{c['file']}:{c['start_line']}-{c['end_line']}] {c['kind']} {qual}\n"
            f"{c['code'][:max_chars]}")

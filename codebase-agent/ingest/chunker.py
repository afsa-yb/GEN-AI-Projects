"""AST-aware chunking: one chunk per function / method / class header,
never splitting a function mid-body. Leftover top-level code (imports,
constants) becomes one 'module' chunk per file."""
import os
from dataclasses import dataclass, asdict
from .parser import language_for, parse_source

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist",
             "build", ".codeagent", ".next", "target", ".tox", ".mypy_cache"}
MAX_FILE_BYTES = 300_000
MAX_CHUNK_CHARS = 6000

_JS_FUNCS = {"function_declaration", "generator_function_declaration", "method_definition"}
FUNC_TYPES = {"python": {"function_definition"},
              "javascript": _JS_FUNCS, "typescript": _JS_FUNCS, "tsx": _JS_FUNCS}
_JS_CLASS = {"class_declaration"}
CLASS_TYPES = {"python": {"class_definition"},
               "javascript": _JS_CLASS, "typescript": _JS_CLASS, "tsx": _JS_CLASS}
WRAPPERS = {"decorated_definition", "export_statement"}
ARROW_TYPES = {"arrow_function", "function_expression", "function"}


@dataclass
class Chunk:
    id: str
    file: str
    name: str
    kind: str          # function | method | class | module
    parent: str        # enclosing class name or ""
    start_line: int
    end_line: int
    language: str
    code: str

    def to_dict(self):
        return asdict(self)


def _text(node) -> str:
    return node.text.decode("utf8", "replace") if node else ""


def chunk_file(rel_path: str, source: bytes, lang: str) -> list[Chunk]:
    tree = parse_source(source, lang)
    funcs, classes = FUNC_TYPES[lang], CLASS_TYPES[lang]
    chunks: list[Chunk] = []

    def outer_of(node):
        p = node.parent
        return p if p is not None and p.type in WRAPPERS else node

    def emit(outer, inner_name, kind, parent, end_byte=None):
        end = end_byte if end_byte is not None else outer.end_byte
        code = source[outer.start_byte:end].decode("utf8", "replace").rstrip()[:MAX_CHUNK_CHARS]
        start_line = outer.start_point[0] + 1
        end_line = (outer.end_point[0] + 1) if end_byte is None else \
            start_line + code.count("\n")
        chunks.append(Chunk(f"{rel_path}:{start_line}:{inner_name}", rel_path,
                            inner_name, kind, parent, start_line, end_line, lang, code))

    def walk(node, parent_class=""):
        t = node.type
        if t in funcs:
            name = _text(node.child_by_field_name("name")) or "<anonymous>"
            emit(outer_of(node), name, "method" if parent_class else "function", parent_class)
            return
        if t in classes:
            name = _text(node.child_by_field_name("name")) or "<anonymous>"
            outer = outer_of(node)
            body = node.child_by_field_name("body")
            first_member = None
            if body is not None:
                for c in body.children:
                    if c.type in funcs or c.type == "decorated_definition":
                        first_member = c.start_byte
                        break
            emit(outer, name, "class", parent_class,
                 end_byte=first_member if first_member else None)
            for c in (body.children if body is not None else []):
                walk(c, name)
            return
        if t in ("lexical_declaration", "variable_declaration") and lang != "python":
            for d in node.children:
                if d.type == "variable_declarator":
                    val = d.child_by_field_name("value")
                    if val is not None and val.type in ARROW_TYPES:
                        emit(outer_of(node), _text(d.child_by_field_name("name")),
                             "function", parent_class)
                        return
        for c in node.children:
            walk(c, parent_class)

    walk(tree.root_node)

    # leftover top-level code (imports, constants) -> one module chunk
    lines = source.decode("utf8", "replace").split("\n")
    covered = set()
    for c in chunks:
        covered.update(range(c.start_line, c.end_line + 1))
    rest = [(i + 1, l) for i, l in enumerate(lines) if (i + 1) not in covered
            and l.strip() and l.strip() not in ("}", "};", ")", "]")]
    if rest:
        code = "\n".join(l for _, l in rest)[:3000]
        stem = os.path.basename(rel_path)
        chunks.append(Chunk(f"{rel_path}:module", rel_path, stem, "module", "",
                            rest[0][0], rest[-1][0], lang, code))
    return chunks


def chunk_repo(repo_path: str) -> list[Chunk]:
    out: list[Chunk] = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            full = os.path.join(root, f)
            lang = language_for(f)
            if not lang or os.path.getsize(full) > MAX_FILE_BYTES:
                continue
            try:
                with open(full, "rb") as fh:
                    src = fh.read()
                out.extend(chunk_file(os.path.relpath(full, repo_path), src, lang))
            except Exception as e:  # one bad file shouldn't kill indexing
                print(f"skip {full}: {e}")
    return out

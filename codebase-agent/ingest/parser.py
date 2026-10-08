"""tree-sitter setup: one Parser per language, picked by file extension."""
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjs
import tree_sitter_typescript as tsts

_LANGS = {
    "python": Language(tspython.language()),
    "javascript": Language(tsjs.language()),
    "typescript": Language(tsts.language_typescript()),
    "tsx": Language(tsts.language_tsx()),
}
_PARSERS = {name: Parser(lang) for name, lang in _LANGS.items()}

EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".ts": "typescript", ".tsx": "tsx",
}


def language_for(path: str) -> str | None:
    for ext, lang in EXT_TO_LANG.items():
        if path.endswith(ext):
            return lang
    return None


def parse_source(source: bytes, lang: str):
    return _PARSERS[lang].parse(source)

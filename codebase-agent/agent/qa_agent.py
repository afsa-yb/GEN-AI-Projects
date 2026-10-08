"""Q&A agent: an LLM + three tools in a loop. The multi-hop tool use
(search -> read symbol -> find callers -> answer) is what makes this an
agent rather than single-shot RAG."""
import json
from retrieval.vectorstore import CodeIndex, format_chunk
from .llm import chat

SYSTEM = """You are a code-intelligence assistant answering questions about one repository.
Rules:
1. Start with search_code to find the relevant functions.
2. Then call get_symbol to read the key function IN FULL before explaining how it works.
   Search snippets are truncated, so never explain code you have only seen in snippets.
3. For "what breaks if I change X" questions: get_symbol(X), then find_usages(X).
4. Usually 2-4 tool calls are enough. Do not repeat similar searches; once you have
   read the relevant code, answer.
5. Cite code as file:start-end. Only describe what you actually saw; if part of the
   code was not visible, say so.
get_symbol accepts 'name', 'Class.method' or 'file.py:name', and can also find small
helper functions defined inside other functions."""


def _tool(name, desc, props, required):
    return {"type": "function", "function": {
        "name": name, "description": desc,
        "parameters": {"type": "object", "properties": props, "required": required}}}


TOOLS = [
    _tool("search_code",
          "Semantic search over the codebase. Returns top matching functions/classes with file:line.",
          {"query": {"type": "string"}}, ["query"]),
    _tool("get_symbol",
          "Fetch full source of a function/method/class by exact name, e.g. 'login' or 'AuthService.login'.",
          {"name": {"type": "string"}}, ["name"]),
    _tool("find_usages",
          "List functions/classes whose body references a symbol name. Use for impact analysis.",
          {"name": {"type": "string"}}, ["name"]),
]

def _run_tool(index: CodeIndex, name: str, args: dict) -> str:
    try:
        if name == "search_code":
            res, per, cap = index.search(str(args["query"]), 4), 900, 4500
        elif name == "get_symbol":
            res, per, cap = index.get_symbol(str(args["name"])), 5000, 9000
        elif name == "find_usages":
            res, per, cap = index.find_usages(str(args["name"]), limit=8), 900, 5000
        else:
            return f"Unknown tool {name}"
    except KeyError as e:
        return f"Missing argument {e}"
    if not res:
        return "No results. Try search_code, or a different name."
    out = "\n\n---\n\n".join(format_chunk(c, per) for c in res)
    return out[:cap]


def ask(index: CodeIndex, question: str, max_steps: int = 6, verbose=None):
    """Returns (answer, trace). `verbose` is an optional callback(str)."""
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": question}]
    trace = []
    for step in range(max_steps):
        msg = chat(messages, TOOLS).choices[0].message
        if not msg.tool_calls:
            return msg.content or "", trace
        messages.append(msg.model_dump(exclude_none=True))
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            line = f"step {step + 1}: {tc.function.name}({args})"
            trace.append(line)
            if verbose:
                verbose(line)
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": _run_tool(index, tc.function.name, args)})
    messages.append({"role": "user",
                     "content": "Step budget reached. Answer now using only what you've gathered."})
    return chat(messages).choices[0].message.content or "", trace

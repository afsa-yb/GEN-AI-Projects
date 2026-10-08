"""codeagent CLI:  index | ask | describe-pr | eval"""
import json
from pathlib import Path
import typer
from rich.console import Console
from rich.markdown import Markdown

app = typer.Typer(add_completion=False, help="Ask questions about a codebase.")
console = Console()


@app.command()
def index(repo: str = typer.Argument(".", help="Path to repo")):
    """Parse the repo with tree-sitter and build the vector index."""
    from retrieval.vectorstore import CodeIndex
    with console.status("Parsing and embedding..."):
        n = CodeIndex(repo).build()
    console.print(f"[green]Indexed {n} chunks[/green] -> {repo}/.codeagent")


@app.command()
def ask(question: str, repo: str = ".", steps: int = 6,
        show_steps: bool = typer.Option(True, help="Print tool calls")):
    """Ask a question about the repo."""
    from retrieval.vectorstore import CodeIndex
    from agent.qa_agent import ask as run
    cb = (lambda s: console.print(f"[dim]{s}[/dim]")) if show_steps else None
    answer, _ = run(CodeIndex(repo), question, max_steps=steps, verbose=cb)
    console.print(Markdown(answer))


@app.command("describe-pr")
def describe_pr(repo: str = ".", base: str = typer.Option(None, help="e.g. main"),
                staged: bool = False):
    """Generate a PR description from your git diff."""
    from agent.pr_agent import describe
    console.print(Markdown(describe(repo, base, staged)))


@app.command("eval")
def eval_(eval_file: str = "tests/eval_set.json", repo: str = ".", k: int = 5):
    """Retrieval hit@k: does a search for each question surface an expected file/symbol?"""
    from retrieval.vectorstore import CodeIndex
    idx = CodeIndex(repo)
    items = json.loads(Path(eval_file).read_text())
    hits = 0
    for it in items:
        res = idx.search(it["question"], k)
        ok = any(r["file"] in it.get("expected_files", []) or
                 r["name"] in it.get("expected_symbols", []) for r in res)
        hits += ok
        console.print(f"{'[green]PASS[/green]' if ok else '[red]FAIL[/red]'}  {it['question']}")
    console.print(f"\n[bold]hit@{k}: {hits}/{len(items)} = {hits / max(len(items), 1):.0%}[/bold]")


if __name__ == "__main__":
    app()

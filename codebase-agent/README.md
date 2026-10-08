# codeagent: ask questions about any codebase

**codeagent** is a command-line tool that reads a code project and answers questions about it in plain English.

```
$ python cli.py ask "where is login handled?" --repo ./my-project
```

It replies with an explanation and points to the exact files and line numbers, like `auth.py:12-30`.
It can also write a **pull request (PR) description** from your code changes.

It runs on a **free** AI provider (Groq, Gemini, or Ollama on your own machine). No paid API needed.

---

## What can it do?

| Command | What it does |
|---|---|
| `index` | Reads your project and builds a searchable index (do this once) |
| `ask` | Answers a question about the code, with file and line citations |
| `describe-pr` | Reads your `git diff` and writes a PR description |
| `eval` | Tests how good the search is, using your own list of questions |

Supports **Python, JavaScript and TypeScript** projects.

---

## How it works 

### Step 1: Index the project (`index`)
1. The tool reads every code file in the project.
2. It cuts each file into pieces. **One piece = one function, method or class.**
   It uses a library called *tree-sitter* that understands code structure, so it never cuts a function in half.
   (A simple tool would cut every 50 lines, which breaks functions and loses meaning.)
3. Each piece is saved with its file name, function name and line numbers.
4. The pieces are stored in two places:
   - **ChromaDB**, a database that finds code by *meaning*. Searching "login" can find `verify_credentials`.
   - **`chunks.json`**, a plain file used to look up a function by its exact name.

### Step 2: Ask a question (`ask`)
Your question goes to an AI model, which can use three tools to explore the code before it answers:

| Tool | What it does |
|---|---|
| `search_code` | Finds functions related to an idea ("auth", "payment") |
| `get_symbol` | Reads one function in full, by name |
| `find_usages` | Shows which other functions mention a name (used for "what breaks if I change X?") |

The AI can use these tools several times in a row. For example: search, then read a function, then see who uses it, then answer.
This looping is what makes it an **agent** rather than a simple search.

### Step 3: PR descriptions (`describe-pr`)
1. It runs `git diff` to get your changes.
2. It works out which functions you changed.
3. It checks who else uses those functions, so it can warn about risks.
4. The AI writes a PR description: Summary, What changed, Why it matters, Risk areas and Suggested tests.

```
Index once:   repo --> split into functions --> search index
Ask:          question --> AI agent <--> 3 tools (search / read / find users) --> answer
PR:           git diff --> changed functions --> who uses them --> AI --> description
```

---

## Project structure

```
codebase-agent/
├── cli.py                  # the commands you type
├── ingest/
│   ├── parser.py           # sets up tree-sitter for each language
│   └── chunker.py          # cuts files into function/class pieces
├── retrieval/
│   ├── embed.py            # turns text into numbers so search works by meaning
│   └── vectorstore.py      # saves pieces and searches them
├── agent/
│   ├── llm.py              # talks to the AI provider (one place for all AI calls)
│   ├── qa_agent.py         # the question-answering loop
│   └── pr_agent.py         # git diff to PR description
├── tests/eval_set.json     # sample questions for measuring search quality
└── requirements.txt        # libraries to install
```

---

## Setup

You need **Python 3.10 or newer**. 

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Pick a free AI provider

The code never changes. You only set three environment variables.

** Groq (hosted, free tier, no download)**
Get a free key at console.groq.com, then:
```bash
export LLM_BASE_URL=https://api.groq.com/openai/v1
export LLM_API_KEY=your-key-here
export LLM_MODEL=qwen/qwen3.8-27b
```

---

## Usage

```bash
# 1. Index a project (once)
python cli.py index /path/to/project

# 2. Ask questions
python cli.py ask "where is authentication handled?" --repo /path/to/project
python cli.py ask "what breaks if I change parse_token?" --repo /path/to/project

# 3. Describe your changes as a PR
python cli.py describe-pr --repo /path/to/project            # all uncommitted changes
python cli.py describe-pr --repo /path/to/project --base main   # compared with main

# 4. Measure search quality
python cli.py eval --repo /path/to/project
```

While `ask` runs you will see the agent's steps, then the final answer:

```
step 1: search_code({'query': 'split files into chunks'})
step 2: get_symbol({'name': 'chunk_file'})
...
(final answer with file:line citations)
```

---

## Limitations

- `find_usages` is a **text match**, not a real call graph. It can miss indirect calls or flag unrelated names.
- Very long functions are cut to 6,000 characters.
- Re-running `index` rebuilds everything (no incremental updates yet).
- Answers depend on the AI model. Smaller or free models sometimes guess about code they did not fully read, so check the citations.
- Free tiers have rate limits. If you hit one, wait a minute and retry.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `command not found: python` | Use `python3` (or activate the venv first) |
| `No module named 'openai'` | Run `pip install -r requirements.txt` with the venv active |
| Terminal shows `dquote>` | A quote was left open. Press Ctrl+C and retype without quotes |
| `model_not_found` (404) | The model name is wrong or retired. List your models with the curl command above |
| `tool_use_failed` | That model writes broken tool calls. Switch `LLM_MODEL` to another model |
| `No index found` | Run `python cli.py index <repo>` first |

---

## Ideas to extend

- Only re-index files that changed
- Combine keyword search with meaning search for better results
- Build a real call graph with tree-sitter queries
- Grade answer quality automatically with an AI judge
- A VS Code extension or a simple web page (Streamlit)

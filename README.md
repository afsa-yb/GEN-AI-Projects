# GEN-AI-Projects
 
A collection of practical **Generative AI** tools and custom chatbots.
Each project lives in its own folder with its own README, so you can open one and run it on its own.
 
Built with **Python, LangChain, Streamlit, tree-sitter, ChromaDB** and open or free-tier language models (Llama, Qwen and others).
 
---
 
## Projects
 
| Project | What it does | Main tech |
|---|---|---|
| [**codebase-agent**](./codebase-agent) | Ask questions about any code repository in plain English and get answers with file and line citations. Also writes PR descriptions from a git diff. | Python, tree-sitter, ChromaDB, LLM tool-calling |
| [**ResearchGPT**](./ResearchGPT) | Chat with a document or research paper: ask a question and get an answer grounded in the text. | Python, embeddings, LLM |
 
---
 
## codebase-agent
 
**The problem:** Joining a large codebase is slow. You need to find where things happen, and what breaks if you change something.
 
**What it does:**
- **`index`** reads a project and splits it into functions, methods and classes (using a code parser, so no function is cut in half).
- **`ask`** answers questions like *"where is login handled?"* or *"what breaks if I change `url_for`?"*, and cites the exact files and lines.
- **`describe-pr`** reads your `git diff` and writes a PR description with a risk section.
**How the agent works:** The AI model has three tools (search the code by meaning, read a function in full, find what uses a name) and can use them several times in a row before answering. That loop is what makes it an agent instead of a simple search.

**Tested on** a real open-source project (Flask, about 1,000 code chunks).
 
---
 
## ResearchGPT
 
Lets you have a conversation with a research paper or document. It reads the text, finds the parts relevant to your question, and uses a language model to answer from them.
  
---
 
## How to run any project here
 
1. Clone the repository:
```bash
   git clone https://github.com/afsa-yb/GEN-AI-Projects.git
   cd GEN-AI-Projects
```
2. Open the project folder you want (`cd codebase-agent`, for example).
3. Follow the README inside that folder. Each project lists its own install steps.
**Tips**
- Use a **virtual environment** for each project so libraries don't clash.
- Never commit API keys. Keep them in environment variables.
- Python 3.10 or newer is recommended.
---
 
## Repository structure
 
```
GEN-AI-Projects/
├── codebase-agent/     # AI Q&A for code repositories
├── ResearchGPT/        # chat with research papers
├── .devcontainer/      # dev container setup
├── LICENSE             # MIT
└── README.md           # this file
```
 
---
 
## License
 
Released under the [MIT License](./LICENSE).
 
---
 
**Author:** Afsa Bhas ([@afsa-yb](https://github.com/afsa-yb)) · bhasafsa@gmail.com
 

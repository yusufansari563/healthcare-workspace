# Agentic AI Workflow System

An end-to-end autonomous agent workflow framework powered by **LangGraph**, **FastAPI**, **PostgreSQL** (Docker), **Local RAG**, **ClickUp Ticketing**, **GitHub PR Creation**, **Email Notifications**, and **Token Cost Optimization** designed for small open-source models.

## Features
- 📋 **AI Planning**: Automatically breaks high-level user instructions into sub-tasks.
- 🎫 **ClickUp Ticketing**: Creates tasks/tickets in ClickUp (Jira equivalent).
- ⚙️ **Task Execution**: Sequentially runs sub-tasks, generating code changes.
- 🤝 **Human-In-The-Loop (HITL)**: Interrupt checkpoints requiring human review for Plan approval and PR approval.
- 🐘 **Postgres State Persistence**: Uses LangGraph `AsyncPostgresSaver` backed by PostgreSQL Docker container.
- 🔍 **Local RAG Vector Store**: Fast, low-token codebase context retrieval with ChromaDB.
- 🔀 **GitHub Integration**: Creates feature branches, commits code, and opens PRs automatically.
- 📧 **Email Notifications**: Sends HTML execution summaries to `yusufansari563@gmail.com`.
- ⚡ **Token Cost Optimization**: Built-in prompt compression, sliding context window trimming, and support for small open-source models (Ollama `llama3.2`, Groq, etc.).
- 🎨 **Web Dashboard UI**: Glassmorphic UI to launch workflows, approve HITL prompts, and monitor execution.

## Quickstart

```bash
# Clone & Navigate
cd agentic-ai-workflow

# Launch via Docker Compose
docker-compose up --build
```

Access the dashboard at **`http://localhost:8000`**.

For detailed setup, environment configuration (`.env`), ClickUp/GitHub/Email credentials, and API documentation, read **[INSTRUCTIONS.md](file:///d:/workspace/healthcare/agentic-ai-workflow/INSTRUCTIONS.md)**.

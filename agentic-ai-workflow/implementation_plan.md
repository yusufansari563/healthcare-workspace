# Implementation Plan - Agentic AI Workflow System

Build an autonomous, human-in-the-loop agentic workflow system using **LangGraph**, **FastAPI**, **PostgreSQL** (Docker), **Local RAG**, **ClickUp Ticketing**, **GitHub PR Creation**, **Email Notifications**, and **Token Cost Optimization** supporting small open-source models (e.g., Ollama, Groq, local models).

## User Review Required

> [!IMPORTANT]
> **3rd Party Integrations & Environment Configuration Needed From User:**
> 1. **ClickUp API**: `CLICKUP_API_KEY` and `CLICKUP_LIST_ID` (for creating tasks/tickets). Mock mode will automatically be used if credentials are not provided.
> 2. **GitHub API**: `GITHUB_TOKEN` and `GITHUB_REPO` (e.g., `username/repo` for raising PRs). Mock mode will automatically be used if credentials are not provided.
> 3. **Email SMTP**: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` (e.g., Gmail App Password for sending notifications to `yusufansari563@gmail.com`). Mock logging will be used if credentials are not provided.
> 4. **LLM Provider**: Supports local **Ollama** (e.g. `llama3.2`, `mistral`, `qwen2.5`), **Groq**, **OpenAI**, or **OpenRouter**.

> [!NOTE]
> The system is designed with **graceful fallbacks**: if any 3rd party service token is missing during initial run, the system operates in **Dry Run / Mock Mode** while fully displaying simulated actions, tickets, PRs, and emails in the dashboard and logs.

---

## Architecture Overview

```
                           +-----------------------------------+
                           |        User Instruction           |
                           +-----------------------------------+
                                             |
                                             v
                           +-----------------------------------+
                           |      Local RAG Vector Store       |
                           |  (Codebase & Doc Search / Context)|
                           +-----------------------------------+
                                             |
                                             v
                           +-----------------------------------+
                           |     1. Planner Node (LangGraph)   |
                           |  (Token-Optimized Small Model LLM)|
                           +-----------------------------------+
                                             |
                                             v
                           +-----------------------------------+
                           | [HITL Interrupt #1] Plan Approval |
                           +-----------------------------------+
                                             |
                                             v
                           +-----------------------------------+
                           |  2. ClickUp Ticket Creator Node   |
                           | (Creates tasks in ClickUp Board)  |
                           +-----------------------------------+
                                             |
                                             v
                           +-----------------------------------+
                           | 3. Ticket Execution Node Loop     |
                           | (Executes tasks, generates code)  |
                           +-----------------------------------+
                                             |
                                             v
                           +-----------------------------------+
                           |  [HITL Interrupt #2] PR Approval  |
                           +-----------------------------------+
                                             |
                                             v
                           +-----------------------------------+
                           | 4. GitHub PR Creation Node        |
                           | (Branches, Commits & Raises PR)   |
                           +-----------------------------------+
                                             |
                                             v
                           +-----------------------------------+
                           | 5. Email Notification Node        |
                           | (Sends email to target address)   |
                           +-----------------------------------+
                                             |
                                             v
                           +-----------------------------------+
                           | Postgres LangGraph Checkpointer   |
                           |    (Docker State Persistence)     |
                           +-----------------------------------+
```

---

## Proposed Changes

### Project Structure (`d:\workspace\healthcare\agentic-ai-workflow`)

```
agentic-ai-workflow/
├── docker-compose.yml              # Docker setup for Postgres DB (with pgvector/LangGraph checkpointer) & FastAPI app
├── Dockerfile                      # App container build file
├── requirements.txt                # Updated dependencies (FastAPI, LangGraph, psycopg, ChromaDB, PyGithub, aiosmtplib)
├── .env.example                    # Environment variable template with documentation
├── README.md                       # High level description & setup overview
├── INSTRUCTIONS.md                 # Detailed step-by-step setup & integration guide
├── src/
│   ├── __init__.py
│   ├── main.py                     # FastAPI server entry point & static UI routing
│   ├── config.py                   # Pydantic Settings & Env configuration
│   ├── database.py                 # Async Postgres connection pool & LangGraph Checkpointer setup
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py                # LangGraph WorkflowState definition
│   │   ├── nodes.py                # Graph nodes: Planner, ClickUp, Executor, PR, Email, RAG
│   │   └── workflow.py             # LangGraph workflow builder with HITL interrupt checkpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_factory.py          # Multi-provider LLM factory (Ollama, OpenAI, Groq, OpenRouter)
│   │   ├── rag_service.py          # Local RAG vector store indexing and retrieval
│   │   ├── clickup_service.py      # ClickUp API ticket creation & management
│   │   ├── github_service.py       # GitHub REST API / PyGithub PR creator
│   │   └── email_service.py        # SMTP Email notifier service
│   ├── utils/
│   │   ├── __init__.py
│   │   └── token_optimizer.py      # Token cost optimization (prompt compression, state trimming, stats tracker)
│   └── static/
│       ├── index.html              # Modern, glassmorphic UI dashboard for workflow execution & HITL approvals
│       └── app.js                  # Interactive dashboard frontend logic
```

---

### Component Details

#### [NEW] [docker-compose.yml](file:///d:/workspace/healthcare/agentic-ai-workflow/docker-compose.yml)
- Sets up PostgreSQL container (`postgres:16-alpine` or `ankane/pgvector`) with health checks.
- Sets up `agentic-app` FastAPI container running on port 8000.

#### [MODIFY] [requirements.txt](file:///d:/workspace/healthcare/agentic-ai-workflow/requirements.txt)
- Adds `fastapi`, `uvicorn`, `psycopg[binary]`, `langgraph-checkpoint-postgres`, `chromadb`, `PyGithub`, `aiosmtplib`, `jinja2`, `python-dotenv`.

#### [NEW] [src/config.py](file:///d:/workspace/healthcare/agentic-ai-workflow/src/config.py)
- Configuration management loading `.env` variables for ClickUp, GitHub, Email, Postgres, and LLM Settings.

#### [NEW] [src/database.py](file:///d:/workspace/healthcare/agentic-ai-workflow/src/database.py)
- Manages Postgres pool connection and LangGraph `AsyncPostgresSaver` checkpointing table initialization.

#### [NEW] [src/utils/token_optimizer.py](file:///d:/workspace/healthcare/agentic-ai-workflow/src/utils/token_optimizer.py)
- Implements prompt compression, token count tracking (prompt/completion tokens), context window clipping for small open-source models (3B/7B/8B params), and cost estimation.

#### [NEW] [src/services/llm_factory.py](file:///d:/workspace/healthcare/agentic-ai-workflow/src/services/llm_factory.py)
- Factory to instantiate LangChain LLM wrappers for local Ollama, Groq, OpenAI, or LiteLLM.

#### [NEW] [src/services/rag_service.py](file:///d:/workspace/healthcare/agentic-ai-workflow/src/services/rag_service.py)
- Uses ChromaDB with local sentence embeddings (`all-MiniLM-L6-v2` or fast lightweight embedder) to index workspace code & documentation for low-token context injection.

#### [NEW] [src/services/clickup_service.py](file:///d:/workspace/healthcare/agentic-ai-workflow/src/services/clickup_service.py)
- Creates ClickUp tasks using the ClickUp v2 API. Supports mock fallback mode when credentials are missing.

#### [NEW] [src/services/github_service.py](file:///d:/workspace/healthcare/agentic-ai-workflow/src/services/github_service.py)
- Creates feature branches, updates/adds files, and opens PRs on GitHub. Supports mock fallback mode.

#### [NEW] [src/services/email_service.py](file:///d:/workspace/healthcare/agentic-ai-workflow/src/services/email_service.py)
- Formats rich HTML emails with execution summaries, ClickUp tickets, PR links, and token savings metrics, then sends via SMTP to `yusufansari563@gmail.com`.

#### [NEW] [src/graph/state.py](file:///d:/workspace/healthcare/agentic-ai-workflow/src/graph/state.py)
- LangGraph state dataclass/TypedDict containing instruction, plan, ClickUp tickets, current task index, code diffs, RAG results, HITL approval flag, PR info, email status, and token metrics.

#### [NEW] [src/graph/nodes.py](file:///d:/workspace/healthcare/agentic-ai-workflow/src/graph/nodes.py)
- Node functions: `rag_node`, `planner_node`, `clickup_node`, `executor_node`, `github_pr_node`, `email_node`.

#### [NEW] [src/graph/workflow.py](file:///d:/workspace/healthcare/agentic-ai-workflow/src/graph/workflow.py)
- LangGraph `StateGraph` compilation with `interrupt_before=["clickup_ticket_creator", "github_pr_creator"]` for human-in-the-loop control.

#### [NEW] [src/main.py](file:///d:/workspace/healthcare/agentic-ai-workflow/src/main.py)
- FastAPI routes: `/api/workflow/start`, `/api/workflow/{thread_id}/approve`, `/api/workflow/{thread_id}/state`, `/api/rag/index`, `/health`. Serves the web dashboard UI.

#### [NEW] [src/static/index.html](file:///d:/workspace/healthcare/agentic-ai-workflow/src/static/index.html) & `app.js`
- Interactive dark-mode web app dashboard showing real-time workflow status, step progress, ClickUp tickets, HITL approval modal, token cost metrics, and log stream.

#### [NEW] [INSTRUCTIONS.md](file:///d:/workspace/healthcare/agentic-ai-workflow/INSTRUCTIONS.md)
- Complete instruction manual detailing how to configure ClickUp API keys, GitHub Tokens, Gmail App Password SMTP, Docker Postgres, Ollama/Open-source models, and API endpoints.

---

## Verification Plan

### Automated Tests & Checks
- Test Python dependencies installation and syntax verification of all modules.
- Run health check endpoint `GET /health`.
- Test LangGraph workflow execution with mock inputs to verify state transitions and HITL interrupts.
- Test Token Optimizer prompt compression utility with sample text inputs.

### Manual Verification
- Test workflow initiation via FastAPI Web UI dashboard.
- Verify HITL approval interface (Approve / Reject step progression).
- Verify ClickUp task payload creation & fallback mock logs.
- Verify GitHub PR creation payload & fallback mock logs.
- Verify Email payload format for `yusufansari563@gmail.com` & SMTP dispatch log.
- Check Docker container orchestration with `docker-compose up`.

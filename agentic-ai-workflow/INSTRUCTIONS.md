# 🚀 Agentic AI Workflow - Comprehensive User Instruction Manual

Welcome to the **Agentic AI Workflow** system! This document provides step-by-step guidance on how to configure, run, and utilize the full end-to-end autonomous agent workflow with **LangGraph**, **FastAPI**, **PostgreSQL (Docker)**, **Local RAG**, **ClickUp Ticketing**, **GitHub PR Creation**, **Email Notifications**, and **Token Cost Optimization**.

---

## 📑 Table of Contents
1. [System Architecture & Workflow Lifecycle](#1-system-architecture--workflow-lifecycle)
2. [Quickstart Guide](#2-quickstart-guide)
3. [Configuration & Environment Setup (.env)](#3-configuration--environment-setup-env)
4. [3rd Party Integrations Setup](#4-3rd-party-integrations-setup)
   - [ClickUp Ticketing](#a-clickup-ticketing-jira-alternative)
   - [GitHub PR Creation](#b-github-pr-creation)
   - [Email SMTP Notifications](#c-email-smtp-notifications-yusufansari563gmailcom)
   - [Ollama & Small Open-Source LLMs](#d-ollama--small-open-source-llms)
5. [Token Cost Optimization](#5-token-cost-optimization)
6. [Interactive Web Dashboard UI](#6-interactive-web-dashboard-ui)
7. [API Endpoints Reference](#7-api-endpoints-reference)

---

## 1. System Architecture & Workflow Lifecycle

```
[User Instruction] ──> [1. Local RAG Retrieval] ──> [2. AI Planner Node]
                                                          │
                                            [HITL Interrupt #1: Plan Approval]
                                                          │
[5. GitHub PR Node] <── [4. Task Executor] <── [3. ClickUp Ticket Creator]
         │
[HITL Interrupt #2: PR Approval]
         │
[6. Email Notification] ──> Sent to yusufansari563@gmail.com
```

### Key Workflow Stages:
1. **Instruction Input & Local RAG Retrieval**: Indexes local codebase files (`.py`, `.md`, `.json`) into ChromaDB to provide relevant context to the model while minimizing token costs.
2. **AI Planning**: Generates a structured 2-4 sub-task execution plan.
3. **Human-In-The-Loop Interrupt #1**: System pauses for user approval of the plan.
4. **ClickUp Ticket Creation**: Automatically creates ticket tasks in ClickUp for each planned sub-task.
5. **Task Execution Loop**: AI executes code changes for each ticket task sequentially.
6. **Human-In-The-Loop Interrupt #2**: System pauses before opening a PR.
7. **GitHub PR Creation**: Creates a git feature branch, commits code changes, and opens a Pull Request on GitHub.
8. **Email Notification**: Dispatches a rich HTML summary report to `yusufansari563@gmail.com` displaying tickets, PR link, and token cost savings.
9. **State Persistence**: Every state transition is automatically saved to PostgreSQL (via LangGraph `AsyncPostgresSaver`).

---

## 2. Quickstart Guide

### Option A: Launch with Docker Compose (Recommended)
Make sure Docker Desktop is installed and running, then execute:

```bash
cd agentic-ai-workflow
docker-compose up --build
```
- **FastAPI Web App & Dashboard**: `http://localhost:8000`
- **PostgreSQL Database (pgvector)**: `localhost:5432`

---

### Option B: Local Python Development Execution

1. **Activate Virtual Environment & Install Dependencies**:
   ```bash
   cd agentic-ai-workflow
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

2. **Copy Environment File**:
   ```bash
   cp .env.example .env
   ```

3. **Start PostgreSQL via Docker (or run local Postgres)**:
   ```bash
   docker-compose up -d postgres
   ```

4. **Launch Application**:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Access dashboard at: **`http://localhost:8000`**

---

## 3. Configuration & Environment Setup (.env)

Edit `.env` to configure 3rd-party integrations and model preferences:

```ini
# PostgreSQL Settings
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=agentic_workflow_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# LLM Choice: ollama, openai, groq, openrouter
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# ClickUp Settings
CLICKUP_API_KEY=pk_12345678_your_key_here
CLICKUP_LIST_ID=901200345

# GitHub Settings
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_REPO=yusufansari563/agentic-ai-workflow

# Email Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yusufansari563@gmail.com
SMTP_PASSWORD=your_gmail_app_password
NOTIFICATION_EMAIL=yusufansari563@gmail.com
```

> [!NOTE]
> **Graceful Fallback Mode**: If any API key (ClickUp, GitHub, or Email) is not provided, the application runs in **Mock/Dry-Run Mode**. It will simulate creating tickets, PRs, and email dispatches in the dashboard logs without failing!

---

## 4. 3rd Party Integrations Setup

### A. ClickUp Ticketing (Jira Alternative)
1. Log in to [ClickUp](https://clickup.com).
2. Go to **Settings -> Apps** -> Generate **Personal API Token** (`pk_...`).
3. Open the ClickUp List where you want tickets created, and copy the `list_id` from the browser URL (`https://app.clickup.com/v/l/li/901200345`).
4. Set `CLICKUP_API_KEY` and `CLICKUP_LIST_ID` in `.env`.

### B. GitHub PR Creation
1. Go to [GitHub Settings -> Personal Access Tokens](https://github.com/settings/tokens).
2. Generate a classic token with `repo` scope (`ghp_...`).
3. Set `GITHUB_TOKEN` and `GITHUB_REPO` (e.g., `yusufansari563/agentic-ai-workflow`) in `.env`.

### C. Email SMTP Notifications (`yusufansari563@gmail.com`)
To send real emails to your inbox:
1. Log in to your Google Account -> **Security -> 2-Step Verification**.
2. Search for **App Passwords** -> Create a new App Password (name it `Agentic Workflow`).
3. Set in `.env`:
   - `SMTP_USER=yusufansari563@gmail.com`
   - `SMTP_PASSWORD=xxxx xxxx xxxx xxxx` (16-digit app password)

### D. Ollama & Small Open-Source LLMs
To run completely offline with small open-source models:
1. Install [Ollama](https://ollama.com).
2. Download model:
   ```bash
   ollama pull llama3.2
   # or mistral, qwen2.5, deepseek-r1:1.5b
   ```
3. Set `LLM_PROVIDER=ollama` in `.env`.

---

## 5. Token Cost Optimization

The system includes a dedicated `TokenOptimizer` module designed for small open-source models (3B/7B/8B params):
- **Prompt Compression**: Removes filler characters, redundant whitespaces, and formatting bloat.
- **RAG Context Trimming**: Clips retrieved workspace context to fit exact token budgets (`max_tokens=1000`).
- **Structured JSON Routing**: Directs the LLM to output concise JSON schemas, avoiding expensive reasoning token churn.
- **Cost Metrics Engine**: Tracks prompt & completion tokens and calculates saved dollars against high-end models ($0.01/1k input).

---

## 6. Interactive Web Dashboard UI

Visit `http://localhost:8000` in your web browser:
1. **Instruction Panel**: Enter your natural language instruction and hit **Launch Agentic Workflow**.
2. **Timeline View**: Visual progress tracker across all 6 workflow steps.
3. **Human-In-The-Loop Modal**: Appears automatically during Plan approval and PR approval. Click **Approve & Continue** to proceed.
4. **Token Cost Card**: Live display of tokens consumed, actual cost, and saved dollars.
5. **Execution Log Stream**: Real-time log terminal.

---

## 7. API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves Interactive Dashboard UI |
| `GET` | `/health` | Returns health status, Postgres & integration state |
| `POST` | `/api/workflow/start` | Starts workflow, returns `thread_id` and initial state |
| `GET` | `/api/workflow/{thread_id}/state` | Fetches current workflow state & pending HITL checkpoint |
| `POST` | `/api/workflow/{thread_id}/approve` | Submits Human-In-The-Loop approval (`approved: true/false`) |
| `POST` | `/api/rag/index` | Re-indexes workspace files into ChromaDB vector store |

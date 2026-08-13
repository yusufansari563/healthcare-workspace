import os
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src.database import get_checkpointer
from src.graph.workflow import compile_agentic_workflow
from src.services.rag_service import rag_service
from src.services.clickup_service import clickup_service
from src.services.github_service import github_service
from src.services.email_service import email_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("main")

app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic AI Workflow API with LangGraph, Docker Postgres, Local RAG, ClickUp, GitHub PR, Email, and Token Cost Optimization.",
    version="1.0.0"
)

# Enable CORS for dashboard UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for Dashboard UI
static_path = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Request Schemas
class WorkflowStartRequest(BaseModel):
    instruction: str
    thread_id: Optional[str] = None

class WorkflowApproveRequest(BaseModel):
    approved: bool = True
    feedback: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Agentic AI Workflow FastAPI Server...")
    # Index workspace directory into RAG service in background
    try:
        rag_service.index_directory(os.getcwd())
    except Exception as e:
        logger.warning(f"RAG indexing on startup warning: {e}")

@app.get("/")
async def root():
    """Serves Dashboard HTML"""
    from fastapi.responses import FileResponse
    index_file = os.path.join(static_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": f"Welcome to {settings.APP_NAME}. Dashboard at /static/index.html"}

@app.get("/health")
async def health():
    """Health check endpoint displaying system state & integration status"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "llm_provider": settings.LLM_PROVIDER,
        "database_host": settings.POSTGRES_HOST,
        "integrations": {
            "clickup": "live" if clickup_service.is_configured() else "mock_mode",
            "github": "live" if github_service.is_configured() else "mock_mode",
            "email": "live" if email_service.is_configured() else "mock_mode"
        }
    }

@app.post("/api/rag/index")
async def index_workspace(directory: Optional[str] = None):
    """Triggers RAG index build for local code & documentation"""
    target_dir = directory or os.getcwd()
    result = rag_service.index_directory(target_dir)
    return {"status": "success", "result": result}

@app.post("/api/workflow/start")
async def start_workflow(req: WorkflowStartRequest):
    """
    Starts a new agentic workflow based on user instruction.
    Executes through RAG retrieval & Planning, then pauses at first HITL interrupt (Plan Review).
    """
    if not req.instruction.strip():
        raise HTTPException(status_code=400, detail="Instruction cannot be empty.")

    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    checkpointer = await get_checkpointer()
    graph_app = compile_agentic_workflow(checkpointer)

    initial_state = {
        "instruction": req.instruction.strip(),
        "plan": [],
        "clickup_tickets": [],
        "execution_results": [],
        "logs": [f"🚀 Workflow initiated with instruction: '{req.instruction}'"]
    }

    # Invoke graph up to first HITL interrupt
    try:
        res_state = await graph_app.ainvoke(initial_state, config=config)
        state_snapshot = await graph_app.aget_state(config)
        
        return {
            "status": "paused_for_approval",
            "thread_id": thread_id,
            "stage": res_state.get("stage", "plan_generated"),
            "next_checkpoint": state_snapshot.next if state_snapshot else [],
            "plan": res_state.get("plan", []),
            "token_usage": res_state.get("token_usage", {}),
            "logs": res_state.get("logs", [])
        }
    except Exception as e:
        logger.exception(f"Error starting workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflow/{thread_id}/state")
async def get_workflow_state(thread_id: str):
    """Fetches full workflow state and pending HITL approval status"""
    config = {"configurable": {"thread_id": thread_id}}
    checkpointer = await get_checkpointer()
    graph_app = compile_agentic_workflow(checkpointer)

    try:
        snapshot = await graph_app.aget_state(config)
        if not snapshot or not snapshot.values:
            raise HTTPException(status_code=404, detail=f"Thread ID '{thread_id}' not found.")

        state_values = snapshot.values
        next_nodes = list(snapshot.next) if snapshot.next else []

        pending_approval = None
        if "clickup_ticket_creator" in next_nodes:
            pending_approval = "plan_approval"
        elif "github_pr_creator" in next_nodes:
            pending_approval = "pr_approval"

        return {
            "thread_id": thread_id,
            "stage": state_values.get("stage", "unknown"),
            "instruction": state_values.get("instruction", ""),
            "plan": state_values.get("plan", []),
            "clickup_tickets": state_values.get("clickup_tickets", []),
            "execution_results": state_values.get("execution_results", []),
            "pr_info": state_values.get("pr_info", {}),
            "email_status": state_values.get("email_status", {}),
            "token_usage": state_values.get("token_usage", {}),
            "logs": state_values.get("logs", []),
            "next_nodes": next_nodes,
            "pending_approval": pending_approval
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow/{thread_id}/approve")
async def approve_workflow_step(thread_id: str, req: WorkflowApproveRequest):
    """
    Human-In-The-Loop approval endpoint.
    Resumes graph execution from current interrupt checkpoint.
    """
    config = {"configurable": {"thread_id": thread_id}}
    checkpointer = await get_checkpointer()
    graph_app = compile_agentic_workflow(checkpointer)

    snapshot = await graph_app.aget_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail=f"Thread ID '{thread_id}' not found.")

    if not req.approved:
        # User rejected - update state log
        logs = snapshot.values.get("logs", [])
        logs.append(f"❌ Step rejected by user. Feedback: {req.feedback or 'No feedback provided'}")
        await graph_app.aupdate_state(config, {"logs": logs, "stage": "rejected_by_human"})
        return {"status": "rejected", "thread_id": thread_id, "message": "Workflow step was rejected by user."}

    # Resume graph execution (passing None signals continuation from interrupt)
    try:
        logger.info(f"Resuming workflow for thread '{thread_id}'...")
        res_state = await graph_app.ainvoke(None, config=config)
        new_snapshot = await graph_app.aget_state(config)

        next_nodes = list(new_snapshot.next) if new_snapshot and new_snapshot.next else []
        pending_approval = None
        if "github_pr_creator" in next_nodes:
            pending_approval = "pr_approval"

        status_str = "completed" if not next_nodes else "paused_for_approval"

        return {
            "status": status_str,
            "thread_id": thread_id,
            "stage": res_state.get("stage"),
            "plan": res_state.get("plan", []),
            "clickup_tickets": res_state.get("clickup_tickets", []),
            "execution_results": res_state.get("execution_results", []),
            "pr_info": res_state.get("pr_info", {}),
            "email_status": res_state.get("email_status", {}),
            "token_usage": res_state.get("token_usage", {}),
            "logs": res_state.get("logs", []),
            "next_nodes": next_nodes,
            "pending_approval": pending_approval
        }
    except Exception as e:
        logger.exception(f"Error resuming workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

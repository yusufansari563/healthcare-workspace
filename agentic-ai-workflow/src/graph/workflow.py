import logging
from langgraph.graph import StateGraph, START, END
from src.graph.state import WorkflowState
from src.graph.nodes import (
    rag_indexing_node,
    planner_node,
    clickup_ticket_creator_node,
    ticket_executor_node,
    github_pr_creator_node,
    email_notifier_node
)

logger = logging.getLogger(__name__)

def create_agentic_workflow_graph():
    """
    Constructs and compiles the LangGraph state graph for the Agentic Workflow system.
    Integrates Human-In-The-Loop (HITL) interrupt checkpoints.
    """
    workflow = StateGraph(WorkflowState)

    # Add Nodes
    workflow.add_node("rag_indexing", rag_indexing_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("clickup_ticket_creator", clickup_ticket_creator_node)
    workflow.add_node("ticket_executor", ticket_executor_node)
    workflow.add_node("github_pr_creator", github_pr_creator_node)
    workflow.add_node("email_notifier", email_notifier_node)

    # Define Linear Edges with Interrupt Checkpoints
    workflow.add_edge(START, "rag_indexing")
    workflow.add_edge("rag_indexing", "planner")
    
    # Pause 1: Plan approval by Human -> proceeds to ClickUp ticket creation
    workflow.add_edge("planner", "clickup_ticket_creator")
    
    workflow.add_edge("clickup_ticket_creator", "ticket_executor")
    
    # Pause 2: PR approval by Human -> proceeds to GitHub PR creation
    workflow.add_edge("ticket_executor", "github_pr_creator")
    
    workflow.add_edge("github_pr_creator", "email_notifier")
    workflow.add_edge("email_notifier", END)

    return workflow

def compile_agentic_workflow(checkpointer):
    """
    Compiles graph with PostgreSQL / Memory checkpointer and HITL interrupt points.
    """
    workflow = create_agentic_workflow_graph()
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["clickup_ticket_creator", "github_pr_creator"]
    )
    logger.info("Successfully compiled LangGraph workflow with HITL interrupts on [clickup_ticket_creator, github_pr_creator].")
    return app

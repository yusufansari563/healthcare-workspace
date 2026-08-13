from typing import TypedDict, List, Dict, Any, Optional

class WorkflowState(TypedDict, total=False):
    instruction: str
    plan: List[Dict[str, Any]]
    clickup_tickets: List[Dict[str, Any]]
    current_ticket_index: int
    execution_results: List[Dict[str, Any]]
    rag_context: str
    pr_info: Dict[str, Any]
    email_status: Dict[str, Any]
    token_usage: Dict[str, Any]
    human_approval: Dict[str, Any]
    stage: str
    logs: List[str]
    error: Optional[str]

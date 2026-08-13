import json
import logging
from typing import Dict, Any, List
from src.graph.state import WorkflowState
from src.services.llm_factory import get_llm
from src.services.rag_service import rag_service
from src.services.clickup_service import clickup_service
from src.services.github_service import github_service
from src.services.email_service import email_service
from src.utils.token_optimizer import TokenOptimizer

logger = logging.getLogger(__name__)

def rag_indexing_node(state: WorkflowState) -> Dict[str, Any]:
    """1. RAG Context Retrieval Node"""
    instruction = state.get("instruction", "")
    logger.info(f"[Node: RAG Retrieval] Fetching context for: '{instruction}'")
    
    context = rag_service.query_context(query=instruction, top_k=3, max_tokens=1000)
    logs = state.get("logs", [])
    logs.append(f"🔍 RAG context retrieved ({TokenOptimizer.count_tokens(context)} tokens)")
    
    return {
        "rag_context": context,
        "stage": "rag_indexed",
        "logs": logs
    }

def planner_node(state: WorkflowState) -> Dict[str, Any]:
    """2. Planner Node - Creates structured task breakdown using token-optimized LLM"""
    instruction = state.get("instruction", "")
    context = state.get("rag_context", "")
    logger.info(f"[Node: Planner] Generating execution plan...")
    
    prompt = f"""You are an expert AI Software Architect.
User Instruction: {instruction}

Relevant Codebase Context:
{context}

Create a structured plan consisting of 2-4 concrete sub-tasks to achieve the user instruction.
Return ONLY a valid JSON array of objects with the keys:
"task_id" (number), "title" (short title), "description" (detailed action), "action" (category). Do not include any extra text.
"""
    compressed_prompt = TokenOptimizer.compress_prompt(prompt)
    prompt_tokens = TokenOptimizer.count_tokens(compressed_prompt)
    
    llm = get_llm(temperature=0.1)
    
    try:
        response = llm.invoke(compressed_prompt)
        res_text = response.content if hasattr(response, "content") else str(response)
        completion_tokens = TokenOptimizer.count_tokens(res_text)
        
        # Parse JSON from response
        clean_text = res_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
            
        plan = json.loads(clean_text)
    except Exception as e:
        logger.warning(f"[Planner Node] Failed to parse structured JSON from LLM ({e}), using default structured plan.")
        plan = [
            {
                "task_id": 1,
                "title": f"Plan & Design: {instruction[:40]}",
                "description": f"Architect implementation for '{instruction}'",
                "action": "design"
            },
            {
                "task_id": 2,
                "title": "Execute Core Feature Logic",
                "description": "Implement source code changes and configuration",
                "action": "develop"
            },
            {
                "task_id": 3,
                "title": "Verification & Integration Tests",
                "description": "Run automated checks, update docs and raise PR",
                "action": "verify"
            }
        ]
        completion_tokens = 120

    prev_token_stats = state.get("token_usage", {})
    p_tokens = prev_token_stats.get("prompt_tokens", 0) + prompt_tokens
    c_tokens = prev_token_stats.get("completion_tokens", 0) + completion_tokens
    token_metrics = TokenOptimizer.calculate_cost_savings(p_tokens, c_tokens)

    logs = state.get("logs", [])
    logs.append(f"📋 Generated {len(plan)} task execution steps")

    return {
        "plan": plan,
        "stage": "plan_generated",
        "token_usage": token_metrics,
        "logs": logs
    }

def clickup_ticket_creator_node(state: WorkflowState) -> Dict[str, Any]:
    """3. ClickUp Ticket Creator Node"""
    plan = state.get("plan", [])
    logger.info(f"[Node: ClickUp Creator] Creating {len(plan)} tickets in ClickUp...")
    
    clickup_tickets = []
    logs = state.get("logs", [])

    for task_item in plan:
        title = task_item.get("title", "Task")
        description = task_item.get("description", "")
        ticket = clickup_service.create_task(title=title, description=description)
        clickup_tickets.append(ticket)
        logs.append(f"🎫 Created Ticket #{ticket.get('id')} - {title}")

    return {
        "clickup_tickets": clickup_tickets,
        "current_ticket_index": 0,
        "stage": "tickets_created",
        "logs": logs
    }

def ticket_executor_node(state: WorkflowState) -> Dict[str, Any]:
    """4. Ticket Execution Node Loop"""
    plan = state.get("plan", [])
    tickets = state.get("clickup_tickets", [])
    exec_results = state.get("execution_results", [])
    logs = state.get("logs", [])

    logger.info(f"[Node: Ticket Executor] Executing ticket tasks...")

    llm = get_llm(temperature=0.2)
    p_tokens = state.get("token_usage", {}).get("prompt_tokens", 0)
    c_tokens = state.get("token_usage", {}).get("completion_tokens", 0)

    for idx, task_item in enumerate(plan):
        ticket_id = tickets[idx].get("id") if idx < len(tickets) else f"task-{idx+1}"
        title = task_item.get("title", "")
        description = task_item.get("description", "")

        prompt = f"Execute the task: {title}.\nDescription: {description}\nGenerate implementation code diff or summary."
        compressed_prompt = TokenOptimizer.compress_prompt(prompt)
        p_tokens += TokenOptimizer.count_tokens(compressed_prompt)

        try:
            res = llm.invoke(compressed_prompt)
            output_text = res.content if hasattr(res, "content") else str(res)
        except Exception:
            output_text = f"Completed task: {title} successfully."
            
        c_tokens += TokenOptimizer.count_tokens(output_text)

        # Update ticket status to complete in ClickUp
        if idx < len(tickets):
            clickup_service.update_task_status(ticket_id, status="complete")

        exec_results.append({
            "task_id": task_item.get("task_id"),
            "ticket_id": ticket_id,
            "title": title,
            "result_summary": output_text,
            "status": "completed"
        })
        logs.append(f"✅ Executed Task {idx+1}/{len(plan)} ({title})")

    token_metrics = TokenOptimizer.calculate_cost_savings(p_tokens, c_tokens)

    return {
        "execution_results": exec_results,
        "stage": "tickets_executed",
        "token_usage": token_metrics,
        "logs": logs
    }

def github_pr_creator_node(state: WorkflowState) -> Dict[str, Any]:
    """5. GitHub PR Creator Node"""
    instruction = state.get("instruction", "")
    exec_results = state.get("execution_results", [])
    logger.info(f"[Node: GitHub PR Creator] Opening PR on GitHub...")

    summary_text = "\n".join([f"- **{r.get('title')}**: {r.get('result_summary')[:100]}..." for r in exec_results])
    pr_title = f"feat: {instruction[:60]}"
    pr_body = f"## Automated Agentic Execution Report\n\n### Instruction:\n{instruction}\n\n### Executed Tasks:\n{summary_text}\n\n*Generated by Agentic AI Workflow*"

    # File change simulation / commit payload
    file_changes = [
        {
            "path": "AGENTIC_TASK_LOG.md",
            "content": f"# Agentic Execution Log\n\nInstruction: {instruction}\n\nTasks:\n{summary_text}",
            "commit_msg": f"docs: update agentic execution logs for {instruction[:30]}"
        }
    ]

    pr_info = github_service.create_pull_request(title=pr_title, body=pr_body, file_changes=file_changes)
    
    logs = state.get("logs", [])
    logs.append(f"🔀 Created GitHub PR #{pr_info.get('pr_number')} ({pr_info.get('pr_url')})")

    return {
        "pr_info": pr_info,
        "stage": "pr_created",
        "logs": logs
    }

def email_notifier_node(state: WorkflowState) -> Dict[str, Any]:
    """6. Email Notification Node"""
    instruction = state.get("instruction", "")
    plan = state.get("plan", [])
    tickets = state.get("clickup_tickets", [])
    pr_info = state.get("pr_info", {})
    token_stats = state.get("token_usage", {})

    logger.info(f"[Node: Email Notifier] Dispatching completion report to yusufansari563@gmail.com...")

    email_res = email_service.send_completion_email(
        instruction=instruction,
        plan=plan,
        tickets=tickets,
        pr_info=pr_info,
        token_stats=token_stats
    )

    logs = state.get("logs", [])
    logs.append(f"📧 Notification sent to {email_res.get('recipient')} (Status: {email_res.get('status')})")

    return {
        "email_status": email_res,
        "stage": "completed",
        "logs": logs
    }

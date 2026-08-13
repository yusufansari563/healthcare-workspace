import asyncio
import logging
from src.database import get_checkpointer
from src.graph.workflow import compile_agentic_workflow

logging.basicConfig(level=logging.INFO)

async def run_test():
    print("--- Testing Agentic AI Workflow Execution ---")
    checkpointer = await get_checkpointer()
    app = compile_agentic_workflow(checkpointer)

    thread_id = "test-thread-101"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "instruction": "Add a rate-limiting middleware to auth-service and update unit tests",
        "plan": [],
        "clickup_tickets": [],
        "execution_results": [],
        "logs": ["Test started"]
    }

    # Step 1: Run to first HITL interrupt (ClickUp creator)
    print("\n1. Invoking Graph (Phase 1: RAG & Planning)...")
    res1 = await app.ainvoke(initial_state, config=config)
    snapshot1 = await app.aget_state(config)
    print(f"Stage: {res1.get('stage')}")
    print(f"Next interrupt node: {snapshot1.next}")
    print(f"Plan generated ({len(res1.get('plan', []))} tasks):")
    for task in res1.get("plan", []):
        print(f"  - [{task.get('task_id')}] {task.get('title')}: {task.get('description')}")

    # Step 2: Resume (Approve Plan -> ClickUp tickets -> Ticket Execution -> Pause before PR)
    print("\n2. Simulating Human Plan Approval & Resuming Execution (Phase 2: Tickets & Execution)...")
    res2 = await app.ainvoke(None, config=config)
    snapshot2 = await app.aget_state(config)
    print(f"Stage: {res2.get('stage')}")
    print(f"Next interrupt node: {snapshot2.next}")
    print(f"ClickUp Tickets created: {len(res2.get('clickup_tickets', []))}")
    for ticket in res2.get("clickup_tickets", []):
        print(f"  - Ticket #{ticket.get('id')}: {ticket.get('name')} ({ticket.get('url')})")

    # Step 3: Resume (Approve PR -> GitHub PR -> Email Notification -> END)
    print("\n3. Simulating Human PR Approval & Resuming Execution (Phase 3: GitHub PR & Email)...")
    res3 = await app.ainvoke(None, config=config)
    snapshot3 = await app.aget_state(config)
    print(f"Final Stage: {res3.get('stage')}")
    print(f"Is Completed: {len(snapshot3.next) == 0}")
    print(f"PR Info: {res3.get('pr_info')}")
    print(f"Email Status: {res3.get('email_status', {}).get('status')}")
    print(f"Token Stats: {res3.get('token_usage')}")
    print("\n--- Test Successfully Completed! ---")


if __name__ == "__main__":
    asyncio.run(run_test())

let currentThreadId = null;

async function checkHealth() {
    try {
        const res = await fetch('/health');
        const data = await res.json();
        console.log("Health status:", data);
    } catch (err) {
        console.warn("Could not fetch health status:", err);
    }
}

function logToTerminal(message, type = 'info') {
    const term = document.getElementById('terminalLog');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    
    let color = '#cbd5e1';
    if (type === 'success') color = '#10b981';
    if (type === 'warning') color = '#f59e0b';
    if (type === 'error') color = '#ef4444';
    
    const timestamp = new Date().toLocaleTimeString();
    entry.style.color = color;
    entry.textContent = `[${timestamp}] ${message}`;
    term.appendChild(entry);
    term.scrollTop = term.scrollHeight;
}

function clearLogs() {
    document.getElementById('terminalLog').innerHTML = '';
}

function updateTimeline(stage) {
    const steps = ['stepRAG', 'stepPlan', 'stepTickets', 'stepExec', 'stepPR', 'stepEmail'];
    steps.forEach(s => {
        const el = document.getElementById(s);
        el.classList.remove('active', 'done');
    });

    if (stage === 'rag_indexed') {
        document.getElementById('stepRAG').classList.add('done');
    } else if (stage === 'plan_generated') {
        document.getElementById('stepRAG').classList.add('done');
        document.getElementById('stepPlan').classList.add('active');
    } else if (stage === 'tickets_created') {
        document.getElementById('stepRAG').classList.add('done');
        document.getElementById('stepPlan').classList.add('done');
        document.getElementById('stepTickets').classList.add('done');
        document.getElementById('stepExec').classList.add('active');
    } else if (stage === 'tickets_executed') {
        document.getElementById('stepRAG').classList.add('done');
        document.getElementById('stepPlan').classList.add('done');
        document.getElementById('stepTickets').classList.add('done');
        document.getElementById('stepExec').classList.add('done');
        document.getElementById('stepPR').classList.add('active');
    } else if (stage === 'completed') {
        steps.forEach(s => document.getElementById(s).classList.add('done'));
    }
}

async function startWorkflow() {
    const instructionInput = document.getElementById('instructionInput');
    const instruction = instructionInput.value.trim();
    if (!instruction) {
        alert("Please enter a valid instruction.");
        return;
    }

    const startBtn = document.getElementById('startBtn');
    startBtn.disabled = true;
    startBtn.textContent = "Processing RAG & Planning...";

    logToTerminal(`Initiating workflow with instruction: "${instruction}"`, 'info');

    try {
        const res = await fetch('/api/workflow/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to start workflow");

        currentThreadId = data.thread_id;
        logToTerminal(`Thread created: ${currentThreadId}`, 'success');

        updateStateView(data);
    } catch (err) {
        logToTerminal(`Error starting workflow: ${err.message}`, 'error');
        alert(`Error: ${err.message}`);
    } finally {
        startBtn.disabled = false;
        startBtn.textContent = "Launch Agentic Workflow";
    }
}

function updateStateView(data) {
    const statusBadge = document.getElementById('workflowStatusBadge');
    statusBadge.textContent = data.stage || "In Progress";

    // Update Logs
    if (data.logs && Array.isArray(data.logs)) {
        data.logs.forEach(l => logToTerminal(l, 'info'));
    }

    // Update Token Metrics
    if (data.token_usage) {
        document.getElementById('statTokens').textContent = (data.token_usage.total_tokens || 0).toLocaleString();
        document.getElementById('statActualCost').textContent = `$${data.token_usage.estimated_actual_cost || 0}`;
        document.getElementById('statSavings').textContent = `$${data.token_usage.saved_dollars || 0}`;
    }

    updateTimeline(data.stage);

    // HITL Card Visibility
    const hitlCard = document.getElementById('hitlCard');
    const hitlMsg = document.getElementById('hitlMessage');

    if (data.next_checkpoint && data.next_checkpoint.includes('clickup_ticket_creator')) {
        hitlMsg.textContent = `The AI planner generated ${data.plan ? data.plan.length : 'several'} sub-tasks. Approve creating ClickUp tickets?`;
        hitlCard.classList.add('visible');
        logToTerminal("⚠️ HITL Pause: Waiting for Plan approval.", 'warning');
    } else if (data.next_nodes && data.next_nodes.includes('github_pr_creator')) {
        hitlMsg.textContent = "All ticket tasks have been executed successfully! Approve creating GitHub Pull Request and sending Email report?";
        hitlCard.classList.add('visible');
        logToTerminal("⚠️ HITL Pause: Waiting for PR & Email approval.", 'warning');
    } else {
        hitlCard.classList.remove('visible');
    }

    if (data.status === 'completed' || data.stage === 'completed') {
        logToTerminal("🎉 Workflow finished successfully! Check your email (yusufansari563@gmail.com).", 'success');
    }
}

async function submitApproval(approved) {
    if (!currentThreadId) return;

    const hitlCard = document.getElementById('hitlCard');
    hitlCard.classList.remove('visible');
    logToTerminal(`Human Approval submitted: ${approved ? 'APPROVED' : 'REJECTED'}`, approved ? 'success' : 'error');

    try {
        const res = await fetch(`/api/workflow/${currentThreadId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ approved })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Approval call failed");

        updateStateView(data);
    } catch (err) {
        logToTerminal(`Error submitting approval: ${err.message}`, 'error');
    }
}

// Initial health check
checkHealth();

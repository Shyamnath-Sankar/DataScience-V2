# 🏗️ Hybrid Architecture: Sheets Copilot + Agentic Chat

## Executive Summary

This architecture **separates concerns** between two distinct modes:

1. **Sheets Copilot**: Fast, direct file editing (NO agents, NO planning)
2. **Agentic Chat**: Complex reasoning with Planner + Skills + Task execution

---

## 📊 BEFORE vs AFTER Comparison

### BEFORE: Monolithic Agent System
```
User Query → Orchestrator → Single Agent → Result
```
**Problems:**
- Every query goes through full agent pipeline (slow)
- No task decomposition for complex analysis
- Sheets edits mixed with analysis logic
- No reusable skill templates
- Poor multi-step reasoning

### AFTER: Hybrid Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    User Request                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Request Type?       │
              └───────────────────────┘
                   │            │
         ┌─────────┘            └──────────┐
         ▼                                  ▼
┌─────────────────┐              ┌──────────────────┐
│  Sheets Copilot │              │   Agentic Chat   │
│  (Fast Path)    │              │   (Complex)      │
└─────────────────┘              └──────────────────┘
         │                                  │
         ▼                                  ▼
┌─────────────────┐              ┌──────────────────┐
│ NL → Pandas     │              │   Orchestrator   │
│ Direct Execute  │              │   Classifies     │
└─────────────────┘              └──────────────────┘
         │                                  │
         │                         ┌────────┴────────┐
         │                    Simple │         Complex
         │                         ▼                 ▼
         │              ┌─────────────┐    ┌─────────────────┐
         │              │ Direct Agent│    │    Planner      │
         │              │ Execution   │    │  (Task Decomposition)
         │              └─────────────┘    └─────────────────┘
         │                                      │
         │                              ┌───────┴───────┐
         │                              ▼               ▼
         │                       ┌──────────┐   ┌──────────────┐
         │                       │  Skills  │   │ Custom Tasks │
         │                       │  Library │   │   (LLM)      │
         │                       └──────────┘   └──────────────┘
         │                              │               │
         │                              └───────┬───────┘
         │                                      ▼
         │                              ┌─────────────────┐
         │                              │  Task Loop:     │
         │                              │  - Execute Task │
         │                              │  - Store Result │
         │                              │  - Check Deps   │
         │                              └─────────────────┘
         │                                      │
         │                                      ▼
         │                              ┌─────────────────┐
         │                              │ Compile Report  │
         │                              └─────────────────┘
         │                                      │
         ▼                                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      Final Output                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Component Details

### 1. Sheets Copilot (Fast Path)
**File:** `services/copilot_service.py`

**Purpose:** Instant spreadsheet edits via natural language

**Flow:**
```
User: "Filter population > 1M"
   ↓
Build Data Context (columns, indices, samples)
   ↓
LLM → JSON Operation (update_cells_bulk, add_column, etc.)
   ↓
Execute Operation on DataFrame
   ↓
Return Updated Grid
```

**Key Features:**
- ❌ NO agents
- ❌ NO planning
- ❌ NO code generation for analysis
- ✅ Direct pandas operations
- ✅ Rich data context (indices, samples, types)
- ✅ JSON validation with retry
- ✅ Revert capability

**Operations Supported:**
- `add_row`, `update_cell`, `update_cells_bulk`
- `delete_rows`, `add_column`, `rename_column`
- Direct Q&A (calculate averages, sums, etc.)

---

### 2. Agentic Chat (Complex Analysis)

#### 2.1 Orchestrator
**File:** `agents/orchestrator.py`

Routes requests to either:
- **Simple Agents** (direct execution)
- **Planner** (multi-step decomposition)

**Routing Logic:**
```python
complex_keywords = ["eda", "machine learning", "model", 
                   "comprehensive", "dashboard", "clean data"]

if any(kw in user_msg for kw in complex_keywords):
    return "planner"
else:
    return classified_intent  # eda/viz/code/sql/general
```

#### 2.2 Skills Library
**File:** `agents/skills.py`

Pre-defined task templates for common workflows:

| Skill | Tasks | Use Case |
|-------|-------|----------|
| **EDA** | 5 tasks (profiling, quality, correlations, distributions, insights) | "Analyze this dataset" |
| **Data Science** | 5 tasks (target ID, preprocessing, training, evaluation, summary) | "Build a prediction model" |
| **Visualization** | 3 tasks (planning, charts, insights) | "Create a dashboard" |
| **Data Cleaning** | 3 tasks (detection, cleaning code, before/after) | "Clean this data" |

**Skill Structure:**
```python
Skill(
    id="eda",
    tasks=[
        TaskTemplate(
            id="eda_1",
            name="Data Profiling",
            prompt_template="Generate Python code to...",
            expected_output_type="data",
            dependencies=[]
        ),
        # ... more tasks
    ]
)
```

#### 2.3 Planner Agent
**File:** `agents/planner.py`

**Responsibilities:**
1. **Plan Creation**: Select skill or generate custom tasks
2. **Task Execution Loop**: 
   - Check dependencies
   - Route to appropriate agent
   - Store results
3. **Report Compilation**: Synthesize all task outputs

**Task Loop Flow:**
```
┌─────────────────┐
│ Execute Task N  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Check Complete? │────No────┐
└────────┬────────┘          │
         │ Yes               │
         ▼                   │
┌─────────────────┐          │
│ Compile Report  │◄─────────┘
└─────────────────┘
```

#### 2.4 Enhanced State
**File:** `agents/state.py`

New fields for planner support:
```python
task_plan: Optional[Dict]       # Current plan with progress
current_task: Optional[Dict]    # Task being executed
task_result: Optional[Dict]     # Last task output
all_tasks_complete: bool        # Loop termination flag
```

---

## 🎯 Graph Flow (LangGraph)

### Simple Query Path
```
START → Orchestrator → EDA/Viz/Code/SQL/General → END
```

### Complex Analysis Path
```
START → Orchestrator → Planner
                      ↓
              ┌───────────────┐
              │ Execute Task  │←──────┐
              └───────┬───────┘       │
                      │               │
                      ▼               │
              ┌───────────────┐       │
              │ Agent Executor│       │
              └───────┬───────┘       │
                      │               │
                      ▼               │
              ┌───────────────┐       │
              │ Complete Task │───────┘
              └───────┬───────┘
                      │ All Done
                      ▼
              ┌───────────────┐
              │ Compile Report│
              └───────┬───────┘
                      │
                      ▼
                     END
```

---

## 📁 File Structure

```
backend/
├── agents/
│   ├── skills.py           # NEW: Skill templates
│   ├── planner.py          # NEW: Planning & task loop
│   ├── state.py            # UPDATED: Added planner fields
│   ├── graph.py            # UPDATED: Dual-mode routing
│   ├── orchestrator.py     # UPDATED: Planner detection
│   ├── eda_agent.py        # Existing (fixed)
│   ├── visualizer_agent.py # Existing (fixed)
│   ├── code_executor.py    # Existing (fixed)
│   ├── sql_agent.py        # Existing (fixed)
│   └── general_agent.py    # Existing (fixed)
│
├── services/
│   ├── copilot_service.py  # Sheets-only (no agents)
│   └── agent_service.py    # Agentic chat runner
│
└── routers/
    ├── copilot.py          # /api/copilot endpoint
    └── agent.py            # /api/agent endpoint
```

---

## 🚀 Usage Examples

### Sheets Copilot (Fast Edits)
```python
# POST /api/copilot
{
  "file_id": "abc123",
  "session_id": "xyz789",
  "message": "Add a column calculating profit as revenue - cost"
}

# Response: Immediate grid update
```

### Agentic Chat (Simple Query)
```python
# POST /api/agent
{
  "file_id": "abc123",
  "session_id": "xyz789",
  "message": "What's the average population?"
}

# Flow: Orchestrator → Code Agent → Execute → Answer
# Time: ~2-3 seconds
```

### Agentic Chat (Complex Analysis)
```python
# POST /api/agent
{
  "file_id": "abc123",
  "session_id": "xyz789",
  "message": "Perform comprehensive EDA on this dataset"
}

# Flow: Orchestrator → Planner → EDA Skill (5 tasks) → Report
# Time: ~15-30 seconds with progress updates
```

---

## ✅ Key Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Sheets Edits** | Mixed with analysis | Dedicated fast path |
| **Complex Analysis** | Single-shot | Multi-step planning |
| **Reusability** | None | Skill library |
| **Error Handling** | Fragile | Retry + dependency management |
| **Progress Tracking** | None | Task-by-task updates |
| **Report Quality** | Generic | Synthesized from multiple analyses |

---

## 🔮 Future Enhancements

1. **More Skills**: Time series, A/B testing, clustering
2. **Human-in-the-Loop**: Approve tasks before execution
3. **Parallel Execution**: Run independent tasks concurrently
4. **Skill Learning**: Auto-generate skills from successful plans
5. **Cost Optimization**: Cache skill results for similar datasets

---

## 🧪 Testing Status

```bash
✓ Skills module loaded: ['eda', 'data_science', 'visualization', 'data_cleaning']
✓ Graph compiled successfully
✓ State schema updated
✓ Planner nodes integrated
```

All components compile and are ready for integration testing!

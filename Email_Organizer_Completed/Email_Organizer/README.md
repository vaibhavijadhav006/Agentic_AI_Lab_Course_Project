# Agentic Email Organizer — Complete 14-Lab Integrated Architecture

An autonomous, multi-agent institutional email processing, triage, and task management system integrating **all 14 practical laboratory concepts** from the Team Worklet Learning Canvas into **ONE unified, cohesive application**.

---

## 🌟 Executive Summary

The **Agentic Email Organizer** transforms passive inbox reading into an autonomous, self-governing multi-agent system. Coordinated by a **Directed Node Graph Orchestrator (Lab 7 DAG)** and a **Parallel Agent Swarm (Lab 8)**, the system deploys **seven main agents** with specialized roles working concurrently on a shared email dataset.

The system incorporates deep contextual research (Lab 9), cloud-native resilience monitoring (Lab 10), automated SDLC CI/CD verification (Lab 11), calendar synchronization, and strict human-in-the-loop safety guardrails (Lab 12) guaranteeing zero unauthorized external communications.

---

## 🚀 Execution Instructions (Windows CMD & PowerShell)

### Prerequisites
- Python 3.10+ (Tested on Python 3.12 64-bit on Windows)
- Dependencies: `python-dotenv>=1.0.0` (Optional: `openai>=1.0.0`)
- **No paid API keys required:** The application includes deterministic local fallbacks and runs 100% offline.

### Single-Command Run
Open Windows Command Prompt (`cmd.exe`) or PowerShell in the project directory:

```cmd
python -m src.main
```
Or simply:
```cmd
python final.py
```
Or double-click:
```cmd
run.bat
```

### Automatic Execution Flow
Upon launching, the application automatically runs through all 14 laboratory concepts in sequence:
1. `[STARTUP]` — Runtime initialization, health checks, storage setup
2. `[EMAIL INGESTION]` — Email retrieval via MCP-style connector
3. `[EMAIL CLASSIFICATION AND PRIORITY]` — Category and urgency scoring
4. `[AGENTIC NODE GRAPH]` — 10-node DAG pipeline execution
5. `[PARALLEL AGENT SWARM]` — Concurrent multi-agent execution
6. `[MEMORY AND RESEARCH]` — Institutional memory and citation retrieval
7. `[DRAFT REPLY GENERATION]` — Contextual response drafting
8. `[ACTION-ITEM EXTRACTION]` — Concrete task isolation
9. `[FOLLOW-UP MANAGEMENT]` — Deadline tracking and reminders
10. `[DOMAIN-SPECIFIC AGENTS]` — Academic, placement, and admin guidance
11. `[SAFETY AND GOVERNANCE]` — PII scanning and approval checks
12. `[FINAL INTEGRATED SYSTEM REPORT]` — Displays Triaged Inbox, Draft Queue, Action Items, and Follow-ups
13. `[INTERACTIVE MODE]` — Enters live interactive menu

---

## 🧠 The Seven Main Agents

Each of the seven main agents performs substantive, verifiable tasks on the shared email dataset:

| # | Agent Name | Class Name | Dedicated Responsibility |
|---|---|---|---|
| **1** | Ingestion and Classification Agent | `IngestionClassificationAgent` | Ingests raw emails from the connector, queries memory for historical sender context, and classifies emails into institutional categories (`academic`, `placement`, `administrative`, `meeting`, `information`). |
| **2** | Priority and Urgency Agent | `PriorityUrgencyAgent` | Evaluates urgency keywords, deadlines, and sender seniority to compute a calibrated urgency score (0–100) and priority level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). |
| **3** | Draft Reply Agent | `DraftReplyAgent` | Generates professional, tailored reply drafts grounded in memory context. Strictly enforces the `PENDING_APPROVAL` status. |
| **4** | Action-Item Extraction Agent | `ActionItemExtractionAgent` | Isolates actionable instructions, report deliverables, and submission deadlines into structured task objects. |
| **5** | Follow-up and Reminder Agent | `FollowupReminderAgent` | Identifies date-bound commitments and builds the follow-up reminder digest for upcoming deadlines. |
| **6** | Calendar and Task Sync Agent | `CalendarTaskSyncAgent` | Detects meeting invitations (e.g. Friday 10 AM review meeting) and registration deadlines, formatting and synchronizing them into the local calendar store. |
| **7** | Archive and Logging Agent | `ArchiveLoggingAgent` | Persists finalized analysis records into SQLite, maintains an immutable audit trail of all operations, and records execution metrics. |

---

## 🗺️ Complete 14-Lab Integration Matrix

All 14 labs operate as connected capabilities within the same workflow:

| Lab # | Laboratory Concept | Integrated Implementation & Evidence |
|---|---|---|
| **Lab 1** | Agent vs Chatbot | Autonomous Goal-Driven Loop (`Observe -> Plan -> Act -> Observe`). Produces structured evidence outputs rather than casual conversational chat. |
| **Lab 2** | Tool-Using Agent | Central `ToolRegistry` (`list_emails`, `get_email`, `save_draft`, `search_memory`, `save_memory`, `deep_research`, `audit_log`, `sync_calendar_event`) with dynamic execution and latency profiling. |
| **Lab 3** | Skill Creation | Modular skills in `EmailSkills`: `classify_email`, `score_priority`, `extract_action_items`, `draft_reply`, and `build_followup_digest`. |
| **Lab 4** | Memory and Retrieval | Persistent SQLite `MemoryStore` (`data/email_memory.db`) storing processed emails, drafts, audit logs, calendar events, and seeded institutional knowledge with keyword/semantic search. |
| **Lab 5** | MCP-Style Connector | Decoupled architecture with `JSONEmailConnector` and `MCPStyleEmailAdapter` exposing standard tool operations (`email.list`, `email.get`, `email.save_draft`). |
| **Lab 6** | Agent Runtime | `AgentRuntime` logging structured execution telemetry to `data/runtime_execution.log`, tracking per-agent invocations, action latencies, and system uptime. |
| **Lab 7** | Agentic Node Graph | Directed DAG orchestrator (`NodeGraphOrchestrator`) coordinating typed state transitions across 10 discrete nodes with zero dropped states. |
| **Lab 8** | Parallel Agent Swarm | Concurrent multi-agent execution using `ThreadPoolExecutor` dispatching discipline specialists concurrently across worker threads with mutex locks. |
| **Lab 9** | Deep Research Agent | Multi-step query expansion and knowledge synthesis (`DeepResearchAgent`) producing cited `ResearchDossier` records referencing institutional guidelines. |
| **Lab 10** | Cloud Operations Agent | `CloudOpsMonitor` providing simulated cloud-native health checks, circuit breaker resilience (`CLOSED`, `HALF_OPEN`, `OPEN`), and error monitoring for college lab runtimes. |
| **Lab 11** | Agentic SDLC Factory | Automated in-pipeline CI/CD testing via `QualityAssuranceAgent`, executing 7 test assertions across schema integrity, boundary checks, and human approval constraints. |
| **Lab 12** | Safety and Governance | `SafetyGovernanceAgent` enforcing zero unauthorized auto-sends, scanning drafts for PII leaks, and requiring explicit human approval (`PENDING_APPROVAL`). |
| **Lab 13** | Discipline-Specific Agents | Domain specialists (`AcademicAdvisorAgent`, `PlacementSpecialistAgent`, `AdministrativeOfficerAgent`) enriching emails with targeted recommendations and refined drafts. |
| **Lab 14** | Final Integrated Capstone | Unified single-command pipeline executing continuously to generate comprehensive audit records, `final.json`, and `final.md`. |

---

## 🎮 Interactive Menu (16 Operational Features)

After automatic execution finishes, the application enters interactive mode automatically. All 16 options are functional:

```text
 1. View All Emails                    -> Formatted table of all inbox emails with priorities
 2. View Email Details                 -> In-depth email viewer with body, classification & research
 3. Search Emails                      -> Full-text search across subject, body, and sender
 4. Generate Reply Draft               -> On-demand reply draft generator for selected email
 5. View Draft Reply Queue             -> Displays all pending and approved drafts with previews
 6. Approve a Draft                    -> Human-in-the-loop approval gate; marks draft APPROVED
 7. Search Memory                      -> Searches SQLite persistent institutional memory
 8. Save Information to Memory         -> Stores arbitrary key-value memory notes
 9. View Action Items                  -> Displays all extracted deliverables by domain
10. View Follow-up Reminders           -> Displays time-sensitive deadlines and reminders
11. Run Agent on Selected Email        -> Dispatches a specific agent on a chosen email
12. View Agent Execution Logs          -> Inspects live runtime telemetry and agent latency metrics
13. View Audit History                 -> Displays immutable governance audit log records
14. View Research Evidence             -> Displays research dossiers, queries, and citations
15. Run Complete Agent Workflow Again  -> Re-executes the full DAG pipeline and refreshes state
16. Exit                               -> Cleanly terminates the application
```

---

## 🛡️ Real Integrations vs Local Fallback Simulations

In accordance with university engineering standards, the project transparently identifies which capabilities use real implementations and which use local fallback simulations:

- **Real Implementations:**
  - Full Python SQLite persistent database engine (`data/email_memory.db`) with relational tables, foreign keys, and thread-safe locking.
  - Multi-threaded concurrent execution using Python `concurrent.futures.ThreadPoolExecutor`.
  - Deterministic regex and NLP rule parsing for category classification, urgency scoring, action item extraction, and PII scanning.
  - In-pipeline CI/CD automated software testing engine with 7 contract assertions.
  - Complete DAG state graph coordinating typed data through 10 stages.
- **Local Fallback Simulations:**
  - **Email Connector:** Uses local JSON file (`data/emails.json`) through the MCP adapter so the project runs offline without requiring IMAP/Gmail credentials.
  - **Cloud Operations:** Simulates cloud-native circuit breakers, SLA latencies, and health checks for college lab runtimes without requiring paid AWS/GCP credentials.
  - **Calendar Sync:** Synchronizes schedule commitments to local SQLite calendar storage (`calendar_events` table) without requiring external Google Calendar API keys.
  - **LLM Drafting:** Uses local deterministic templates if `OPENAI_API_KEY` is not present, ensuring 100% functionality without internet or API costs.

---

## 🧪 Automated Test Suite

Run the full automated test suite using Python's built-in `unittest` runner:

```cmd
python -m unittest discover tests
```

### Test Results
```text
Ran 24 tests in 0.381s

OK
```
All 24 unit and integration tests pass with 100% success rate:
- `test_labs_1_to_5.py`: 5 tests covering connector, adapter, skills, memory, and tools.
- `test_seven_agents.py`: 7 tests verifying each of the 7 main agents operates on shared data.
- `test_all_14_labs.py`: 9 tests verifying telemetry, graph, swarm, research, cloud ops, SDLC, safety, discipline agents, and capstone report.
- `test_interactive_menu.py`: 3 tests verifying draft approval, memory queries, and search.

---

## 📊 Deliverables Summary

- **Primary Launcher:** [`final.py`](file:///C:/Users/vaibh/.gemini/antigravity/scratch/Email_Organizer/final.py) (or `python -m src.main`)
- **Final JSON Report:** [`final.json`](file:///C:/Users/vaibh/.gemini/antigravity/scratch/Email_Organizer/final.json)
- **Final Markdown Report:** [`final.md`](file:///C:/Users/vaibh/.gemini/antigravity/scratch/Email_Organizer/final.md)
- **Persistent Database:** [`data/email_memory.db`](file:///C:/Users/vaibh/.gemini/antigravity/scratch/Email_Organizer/data/email_memory.db)
- **Runtime Log:** [`data/runtime_execution.log`](file:///C:/Users/vaibh/.gemini/antigravity/scratch/Email_Organizer/data/runtime_execution.log)
- **Complete Submission Zip:** [`Email_Organizer_Completed.zip`](file:///C:/Users/vaibh/.gemini/antigravity/scratch/Email_Organizer_Completed.zip)

# TeamTasks - Infrastructure Task Management System

A modern, bilingual (Hebrew/English) task and project management platform built with Python & Flask, tailored for Infrastructure and DevOps teams. Features an intelligent natural-language AI Assistant, dual AI engine support (Local/Air-Gapped Ollama or Cloudflare Workers AI), real-time live synchronization, an advanced workload calendar, a collection of 30 3D superhero avatars, and automated CI/CD deployment to Docker Hub and GCP.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.1+-green.svg)
![MCP Server](https://img.shields.io/badge/MCP%20Server-37%20Tools-purple.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![WSGI](https://img.shields.io/badge/server-gunicorn-orange.svg)

---

## 📋 Table of Contents

- [Features](#-features)
  - [🤖 AI Assistant & Automation](#-ai-assistant--automation)
  - [📋 Core Task & Project Management](#-core-task--project-management)
  - [📅 Calendar & Workload Planning](#-calendar--workload-planning)
  - [🦸 3D Avatars & Customization](#-3d-avatars--customization)
  - [⚙️ Admin & System Diagnostics](#-admin--system-diagnostics)
  - [💾 Backup & Restore](#-backup--restore)
- [Architecture & AI Engine](#-architecture--ai-engine)
- [🔌 Model Context Protocol (MCP) Server](#-model-context-protocol-mcp-server)
  - [Supported Transports](#supported-transports)
  - [Agent Client Setup Examples](#agent-client-setup-examples)
  - [Complete MCP Tool Catalog (37 Tools)](#complete-mcp-tool-catalog-37-tools)
  - [MCP Resources & Prompts](#mcp-resources--prompts)
  - [Interactive Admin Panel Tester](#interactive-admin-panel-tester)
- [Screenshots](#-screenshots)
- [Quick Start](#-quick-start)
- [Configuration (.env)](#-configuration-env)
- [Deployment](#-deployment)
  - [Docker](#docker)
  - [Docker Compose](#docker-compose)
  - [CI/CD Automated Deployment](#cicd-automated-deployment)
  - [Kubernetes/OpenShift](#kubernetesopenshift)
- [API Documentation](#-api-documentation)
  - [AI Assistant API](#ai-assistant-api)
  - [System Settings & Diagnostics API](#system-settings--diagnostics-api)
  - [Tasks API](#tasks-api)
  - [Teams & Members API](#teams--members-api)
  - [Backup & Restore API](#backup--restore-api)
- [🆕 Recent Updates & Changelog](#-recent-updates--changelog)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🤖 AI Assistant & Automation
- 🔌 **Built-in MCP Server (Model Context Protocol)** - Full 37-tool MCP Server (`mcp_server.py` + `/mcp` HTTP/SSE endpoints) allowing external AI Agents (Antigravity, Claude Desktop, Cursor, Windsurf, VS Code Copilot) to manage tasks, projects, teams, members, calendar schedules, workloads, and backups.
- 💬 **Bilingual Natural Language Chat** - Interact in natural Hebrew or English directly in a slide-out assistant panel.
- ⚡ **Full Free-Text System Management** - Create, update, reassign, postpone, complete, archive, or delete tasks and projects using natural conversational prompts (e.g. *"תשני את המשימה 82 בתהליך"*, *"תוסיף משימה דחופה לפרויקט אבטחה"*).
- 🧠 **Dual AI Provider Architecture**:
  - **Local & Air-Gapped AI**: Compatible with local LLM gateways (Ollama, vLLM, LocalAI) using standard OpenAI API format (zero external data leaks).
  - **Cloudflare Workers AI**: Serverless cloud option using `@cf/meta/llama-3.1-8b-instruct`.
- 🛡️ **Built-in Guardrails & Fallbacks** - Deterministic validation ensures the LLM never executes hallucinated mutations or invents non-existent entity IDs.
- 📊 **Executive Insights & Deadline Monitoring** - Instant executive summaries, delayed task alerts, and workload distribution breakdowns.
- 🔄 **Conversational Memory** - Remembers referenced tasks, ordinals (*"הראשונה"*, *"השנייה"*), and follow-up commands across the conversation.

### 📋 Core Task & Project Management
- ✅ **Task Management** - Create, edit, prioritize, assign, and track tasks.
- 👥 **Team & Member Scoping** - Filter by Team, Member, Project, Status, and Priority across all views.
- 🎯 **Advanced Status & Priority Filtering** - Filter by Status (*Not Started*, *In Progress*, *Done*, *Delayed*) and Priority (*High*, *Medium*, *Low*, *None*), plus the new **"All except done" (`not-done` / הכל למעט הושלם)** filter to quickly isolate active work.
- 🧹 **One-Click Clear Filters ("נקה סינון")** - Instant reset for all active filter dimensions on Dashboard and Calendar.
- 📦 **Task & Project Archiving** - Dedicated archive view with one-click restore.
- 🖨️ **Printable Reports** - Clean, scoped printable summaries with instant filtering.

### 📅 Calendar & Workload Planning
- 🗓️ **Weekly & Monthly Views** - Drag-and-drop planning and deadline tracking.
- ⚖️ **Workload Capacity View** - Real-time workload analysis per team member.
- 🎈 **Special Days & Holidays** - Manage organizational holidays and events with custom colors.

### 🦸 3D Avatars & Customization
- 🎨 **30 Built-in 3D Clay Avatars** - High-resolution characters including:
  - Superhero collection: Superman, Batman, Spider-Man, Iron Man, Wonder Woman, Hulk, Captain America, Flash, Deadpool, Goku, etc.
  - Fun cartoons & mascots: SpongeBob, Pikachu, Ninja, Mario, Sonic, Minion, Ninja Turtle, Baby Yoda (Grogu), and more.
- 🖼️ **Custom Avatar Uploads** - Built-in avatar picker and image uploader.

### ⚙️ Admin & System Diagnostics
- 🛠️ **General Settings ("הגדרות כלליות")** - Live configuration manager for `.env` settings:
  - Toggle between Local AI Gateway and Cloudflare.
  - Change model names and base endpoints on-the-fly without restart.
  - Test AI connectivity with real-time latency diagnostics.
- 🩺 **System Diagnostics & Health** - Database size calculation, SQLite integrity check (`PRAGMA integrity_check`), uploads storage metrics, and active process runtime metrics.

### 💾 Backup & Restore
- 📦 **Full System JSON Backup** - Export all tables (teams, members, projects, tasks, associations, special days) in a single JSON package.
- 🔄 **Atomic Restore** - One-click full restore with foreign key preservation, or single-table restore.

---

## 🏛️ Architecture & AI Engine

```
                     ┌──────────────────────────────────────┐
                     │          Browser Frontend            │
                     │  (Vanilla JS, Tailwind, Live Sync)   │
                     └──────────────────┬───────────────────┘
                                        │ HTTP / REST
                                        ▼
                     ┌──────────────────────────────────────┐
                     │          Flask WSGI App              │
                     │      (Gunicorn Production)           │
                     └───────┬──────────────────────┬───────┘
                             │                      │
                 Tool Calls  │                      │ System Context
                 & Actions   ▼                      ▼
        ┌──────────────────────────┐      ┌─────────────────────────┐
        │  ai_tools.py (Guardrails)│      │    ai_context.py        │
        │  - Fallback Intent       │      │  - Active Tasks & Teams │
        │  - Hallucination Filter  │      │  - Deadlines & Workload │
        │  - Database Mutations    │      │  - Hebrew Formatter     │
        └────────────┬─────────────┘      └────────────┬────────────┘
                     │                                 │
                     └────────────────┬────────────────┘
                                      │ Prompt + Schema
                                      ▼
                     ┌──────────────────────────────────────┐
                     │             ai_service.py            │
                     │  ┌────────────────────────────────┐  │
                     │  │ Local / Air-Gapped Gateway     │  │
                     │  │ (Ollama, vLLM, LocalAI)        │  │
                     │  ├────────────────────────────────┤  │
                     │  │ Cloudflare Workers AI          │  │
                     │  │ (@cf/meta/llama-3.1-8b)        │  │
                     │  └────────────────────────────────┘  │
                     └──────────────────────────────────────┘
```

---

## 🔌 Model Context Protocol (MCP) Server

TeamTasks features a first-class, production-grade **Model Context Protocol (MCP)** server ([`mcp_server.py`](file:///d:/projects/teamtasks/mcp_server.py)), allowing external AI Agents—such as **Google Antigravity**, **Anthropic Claude Desktop**, **Cursor**, **Windsurf**, and **VS Code Copilot**—to programmatically inspect, query, schedule, and manipulate the entire task management platform.

### Key Highlights
- 🧰 **37 Comprehensive Tools**: Full CRUD on Tasks, Projects, Teams, Members, Calendar, Workloads, Analytics, and Backups.
- 📦 **9 Live Resources**: Instant read-only context URIs (`teamtasks://...`) for quick agent grounding without multiple roundtrips.
- 💬 **4 Specialized Prompts**: Pre-engineered workflows (`morning_standup`, `deadline_audit`, `workload_rebalance`, `sprint_planning`).
- ⚡ **Multi-Transport Support**: Run locally via standard input/output (`stdio`), stream over HTTP (`/mcp`), or connect via Server-Sent Events (`/mcp/sse`).
- 🔒 **Security & Authentication**: Optional Bearer token protection (`MCP_API_KEY`) for remote endpoints.
- 🧪 **Interactive Web Tester**: Built-in Admin UI (`/admin#mcp`) for testing any tool with visual forms and copying client configurations with one click.

---

### Supported Transports

| Transport | Command / Endpoint | Typical Use Case |
| :--- | :--- | :--- |
| **Stdio (Local CLI)** | `python mcp_server.py` | Local Desktop AI Agents (Claude Desktop, Cursor, Antigravity) |
| **Streamable HTTP** | `POST http://localhost:5000/mcp` | Stateless JSON-RPC 2.0 requests from remote orchestrators |
| **Server-Sent Events (SSE)** | `GET http://localhost:5000/mcp/sse`<br>`POST http://localhost:5000/mcp/messages` | Streaming agent platforms and containerized remote clients |

---

### Agent Client Setup Examples

#### 1. Anthropic Claude Desktop
Add to your `claude_desktop_config.json` (`%APPDATA%\Claude\claude_desktop_config.json` on Windows or `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "teamtasks": {
      "command": "python",
      "args": ["/absolute/path/to/teamtasks/mcp_server.py"],
      "env": {
        "TEAMTASKS_DB_PATH": "/absolute/path/to/teamtasks/instance/tasks.db"
      }
    }
  }
}
```

#### 2. Cursor & Windsurf
Add to your project's `.cursor/mcp.json` or global MCP settings:

```json
{
  "mcpServers": {
    "teamtasks": {
      "command": "python",
      "args": ["d:/projects/teamtasks/mcp_server.py"]
    }
  }
}
```

#### 3. Remote HTTP / SSE Client (e.g. Antigravity / Containerized Agent)
Connect directly to the running Flask server over network:

```json
{
  "mcpServers": {
    "teamtasks-remote": {
      "url": "http://localhost:5000/mcp/sse",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_API_KEY"
      }
    }
  }
}
```

---

### Complete MCP Tool Catalog (37 Tools)

#### 📋 Tasks (10 Tools)
- `list_tasks` - Query tasks with multi-dimensional filters (`team_id`, `member_id`, `project_id`, `status` including `not-done`, `priority`, `search_query`, `limit`, `offset`).
- `get_task` - Retrieve comprehensive task details including assignees, projects, and timestamps.
- `create_task` - Create a new task with title, description, team, project, assignees, dates, and priority.
- `update_task` - Update any task property (title, description, team, project, status, priority, assignees, dates).
- `update_task_schedule` - Quickly reschedule or postpone a task (update `start_date` and `due_date`).
- `archive_task` - Move task to archive (soft delete).
- `unarchive_task` - Restore an archived task to active status.
- `delete_task` - Permanently remove task from database.
- `bulk_update_tasks` - Atomically batch update status, team, project, or priority across multiple task IDs.
- `search_tasks` - Full-text search across task titles and descriptions.

#### 📁 Projects (6 Tools)
- `list_projects` - List all projects with active task counts and associated teams.
- `get_project` - Retrieve project details, team associations, and all associated tasks.
- `create_project` - Create a new project with optional team assignments.
- `update_project` - Rename, update description, or modify team links for an existing project.
- `archive_project` - Move project to archive.
- `delete_project` - Permanently delete project.

#### 👥 Teams (4 Tools)
- `list_teams` - List all organizational teams, their members, and workload metrics.
- `create_team` - Create a new team with an optional hex color code.
- `update_team` - Rename team or adjust its brand color.
- `delete_team` - Delete team with safe fallback handling.

#### 🦸 Team Members & Avatars (5 Tools)
- `list_members` - List all members with team affiliations, email, role, and avatar.
- `create_member` - Add new team member with avatar selection and team assignments.
- `update_member` - Update member name, email, role, avatar, or team associations.
- `delete_member` - Remove member from system.
- `list_avatars` - Retrieve full catalog of 30 predefined 3D superhero and mascot avatar files.

#### 📅 Calendar & Workload Planning (6 Tools)
- `get_calendar_week` - Fetch weekly task schedule and special days for any target date.
- `get_calendar_month` - Fetch full monthly view with date-grouped task distributions.
- `get_member_workload` - Calculate real-time task load and capacity per team member.
- `list_special_days` - List holidays, corporate events, and off-days.
- `create_special_day` - Register a holiday or special day with date range and badge color.
- `delete_special_day` - Remove a special day by ID.

#### 📊 Analytics, Diagnostics & Backups (6 Tools)
- `get_executive_summary` - High-level executive dashboard: total tasks, status breakdowns, delayed counts, completion rate, and workload.
- `get_deadlines_analysis` - Proactive deadline audit: overdue tasks, tasks due today, and tasks due in the next 3 days.
- `get_stale_and_suggestions` - Identify stale/inactive tasks and receive intelligent optimization suggestions.
- `get_system_diagnostics` - Database size, SQLite integrity (`PRAGMA integrity_check`), table row counts, and upload metrics.
- `export_system_backup` - Generate complete JSON system backup package (all tables or scoped by table).
- `restore_system_backup` - Restore database tables atomically from a JSON backup payload.

---

### MCP Resources & Prompts

#### Resources (`teamtasks://...`)
Agents can attach live context URIs without invoking tool calls:
- `teamtasks://tasks/active` - Snapshot of all currently active tasks.
- `teamtasks://tasks/summary` - Aggregated status counts and metrics.
- `teamtasks://projects/active` - List of all ongoing projects.
- `teamtasks://teams/all` - Complete organizational team directory.
- `teamtasks://members/all` - Member list with assigned teams and roles.
- `teamtasks://calendar/current-week` - Current week's scheduled tasks.
- `teamtasks://calendar/current-month` - Current month's scheduled tasks.
- `teamtasks://system/diagnostics` - Health status and database storage metrics.
- `teamtasks://schema/openapi` - System entity relationship models and schemas.

#### Prompts
Pre-engineered prompts for common DevOps workflows:
- `morning_standup` - Generates a daily standup brief for a team or member.
- `deadline_audit` - Evaluates overdue and at-risk deadlines with proposed action steps.
- `workload_rebalance` - Analyzes member capacities and suggests balanced task reassignments.
- `sprint_planning` - Guides scheduling backlog items into upcoming calendar weeks.

---

### Interactive Admin Panel Tester

Navigate to **Admin Panel → שרת MCP (AI Agents)** (`http://localhost:5000/admin#mcp`):
1. **Interactive Runner**: Select any of the 37 MCP tools, enter parameters into dynamic input fields, and inspect JSON responses in real-time.
2. **One-Click Config Generator**: Instantly copy customized configuration snippets for Claude Desktop, Cursor, or SSE clients.
3. **API Key Management**: Set or update your `MCP_API_KEY` directly from the UI without restarting the container.

---

### Prerequisites
- Python 3.10+
- pip

### 1. Clone & Install
```bash
git clone https://github.com/devopsteamsdb/teamtasks.git
cd teamtasks
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` to configure your AI provider (Local Ollama or Cloudflare):
```ini
AI_PROVIDER=local_openai
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_MODEL=llama3.3
```

### 3. Run Development Server
```bash
python app.py
```
Visit:
- **Dashboard:** http://localhost:5000
- **Admin Panel:** http://localhost:5000/admin
- **Calendar:** http://localhost:5000/calendar

---

## ⚙️ Configuration (.env)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `APP_NAME` | Display name of the application | `TeamTasks` |
| `FLASK_APP` | Flask application entry point | `app.py` |
| `FLASK_DEBUG` | Enable debug mode (`1` or `0`) | `0` |
| `AI_PROVIDER` | Active AI provider (`local_openai` or `cloudflare`) | `local_openai` |
| `OPENAI_API_BASE` | Local or OpenAI-compatible endpoint URL | `http://localhost:11434/v1` |
| `OPENAI_MODEL` | Local LLM model identifier | `llama3.3` |
| `OPENAI_API_KEY` | Optional API key for Local Gateway / OpenAI | *empty* |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Account ID | *empty* |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token | *empty* |
| `CLOUDFLARE_MODEL` | Cloudflare Workers AI model tag | `@cf/meta/llama-3.1-8b-instruct` |
| `MCP_API_KEY` | Optional Bearer authorization token for remote MCP endpoints (`/mcp`, `/mcp/sse`) | *empty (open access)* |
| `TEAMTASKS_API_URL` | Base API URL when running MCP server in remote proxy mode | *empty (direct SQLite mode)* |

---

## 📦 Deployment

### Docker

#### Run Pre-built Image from Docker Hub
```bash
docker run -d \
  -p 5000:5000 \
  -v /var/teamtasks/db:/app/instance \
  -v /var/teamtasks/uploads:/app/uploads \
  --name teamtasks \
  --restart unless-stopped \
  devopsteamsdb/devopsteamsdb:teamtasks_latest
```

#### Build Local Docker Image
```bash
docker build -t teamtasks:latest .
docker run -d -p 5000:5000 -v $(pwd)/instance:/app/instance teamtasks:latest
```

### Docker Compose
Deploy easily with persistent storage:

```yaml
version: '3.8'

services:
  teamtasks:
    image: devopsteamsdb/devopsteamsdb:teamtasks_latest
    container_name: teamtasks
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - FLASK_DEBUG=0
      - FLASK_APP=app.py
      - AI_PROVIDER=local_openai
      - OPENAI_API_BASE=http://host.docker.internal:11434/v1
      - OPENAI_MODEL=llama3.3
    volumes:
      - ./instance:/app/instance
      - ./uploads:/app/uploads
```

```bash
docker compose up -d
```

### CI/CD Automated Deployment

The repository includes GitHub Actions workflows configured in `.github/workflows/`:
1. **Docker Image CI (`docker-image.yml`):**
   - Triggers on push to `main`.
   - Builds timestamped and `teamtasks_latest` multi-platform Docker images.
   - Pushes to Docker Hub (`devopsteamsdb/devopsteamsdb`).
   - Generates a GitHub Release with an image artifact archive.
2. **Deploy to GCP (`gcp.yml`):**
   - Automatically triggered after Docker Image CI succeeds.
   - Resolves target GCP server IP.
   - Verifies SSH port connectivity.
   - Pulls the latest container and executes zero-downtime container replacement.
   - Verifies deployment health.

---

## 📡 API Documentation

### AI Assistant API

#### 1. Chat with AI Assistant & Execute Free-Text Actions
```http
POST /api/ai/chat
Content-Type: application/json

{
  "message": "תשני את המשימה 82 בתהליך",
  "history": [
    {"role": "user", "content": "מה המשימות הפתוחות של צוות DEVOPS?"},
    {"role": "assistant", "content": "להלן 14 משימות פתוחות..."}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "reply": "",
  "actions": [
    {
      "action": "edit_task",
      "status": "success",
      "task_id": 82,
      "description": "עודכנה משימה #82: 'שדרוג פרודקשן'"
    }
  ],
  "refresh_needed": true
}
```

#### 2. Get AI Engine Status
```http
GET /api/ai/status
```

---

### System Settings & Diagnostics API

#### 1. Get Settings & Runtime Metrics
```http
GET /api/system/settings
```
Returns system configuration, masked tokens, database metrics, storage size, active project/task counts, and runtime information.

#### 2. Update .env Settings Live
```http
POST /api/system/settings
Content-Type: application/json

{
  "ai_provider": "local_openai",
  "openai_base_url": "http://localhost:11434/v1",
  "openai_model": "llama3.3"
}
```

#### 3. Test AI Connection
```http
POST /api/system/test-ai
Content-Type: application/json

{
  "provider": "local_openai",
  "openai_base_url": "http://localhost:11434/v1",
  "openai_model": "llama3.3"
}
```

#### 4. Database Integrity Check
```http
POST /api/system/check-db
```
Executes SQLite `PRAGMA integrity_check`.

---

### Tasks API

- `GET /api/tasks` - List all tasks (supports query filtering by `project`, `team_id`, `status`).
- `POST /api/tasks` - Create a new task.
- `PUT /api/tasks/{id}` - Update task details or status.
- `DELETE /api/tasks/{id}` - Delete task.
- `POST /api/tasks/{id}/archive` - Move task to archive.
- `POST /api/tasks/{id}/unarchive` - Restore task from archive.

### Backup & Restore API

- `GET /api/backup/{table_name}` - Download JSON backup (`table_name`: `all`, `tasks`, `projects`, `teams`, `members`, `special_days`).
- `POST /api/restore/{table_name}` - Upload and restore JSON backup.

---

### MCP (Model Context Protocol) Endpoints

- `POST /mcp` - Streamable JSON-RPC 2.0 MCP endpoint for AI Agents.
- `GET /mcp/sse` - Server-Sent Events (SSE) streaming transport for MCP agents.
- `POST /mcp/messages` - SSE client message receiver endpoint.
- For complete transport details, tool catalogs, and agent client configurations, see the dedicated [🔌 Model Context Protocol (MCP) Server](#-model-context-protocol-mcp-server) section.

---

## 🆕 Recent Updates & Changelog

### v2.2.0 (Latest Release)
- 🔌 **Full Model Context Protocol (MCP) Integration**:
  - Implemented standalone `mcp_server.py` supporting both `stdio` and remote HTTP/SSE transports (`/mcp`, `/mcp/sse`).
  - **37 production-grade MCP tools** for complete agentic automation of Tasks, Projects, Teams, Members, Calendar, Workloads, Analytics, and Backups.
  - **9 live MCP Resources** (`teamtasks://...`) and **4 specialized Prompts** (`morning_standup`, `deadline_audit`, `workload_rebalance`, `sprint_planning`).
  - Dedicated interactive **MCP Admin Panel** (`/admin#mcp`) with dynamic parameter forms, live response preview, and auto-generated client configurations.
  - Optional Bearer token security via `MCP_API_KEY`.
- 🎯 **Advanced Status & Priority Filtering ("Not-Done" View)**:
  - Added **"הכל למעט הושלם" (`not-done`)** status filter across Dashboard, Calendar, and Print views to quickly focus on active workloads.
  - Added instant **"נקה סינון" (Clear Filters)** button to reset all active filter dimensions in one click.
  - Integrated `not-done` filtering capability into AI Assistant intent handlers.
- ⚡ **Stability & Frontend Performance**:
  - Fixed ES module variable scoping (`urlParams`) and ensured resilient event listener registration.
  - Implemented automated asset cache-busting (`v=5`) for immediate client updates.

### v2.1.0
- 🤖 **Bilingual Natural-Language AI Assistant**:
  - Dual AI engine support: Local/Air-gapped LLMs (Ollama, vLLM) and Cloudflare Workers AI.
  - Deterministic guardrails against hallucinations and invalid database mutations.
- 🦸 **30 3D Clay Avatars**:
  - Built-in superhero and mascot avatar suite with custom upload support.
- 🩺 **Admin Diagnostics & Live Configuration**:
  - Real-time `.env` live configuration management directly from the web interface without restarting the server.
  - SQLite integrity diagnostics and database metrics.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

**Made with ❤️ for DevOps & Infrastructure Teams**

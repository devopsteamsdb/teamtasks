# TeamTasks - Infrastructure Task Management System

A modern, bilingual (Hebrew/English) task and project management platform built with Python & Flask, tailored for Infrastructure and DevOps teams. Features an intelligent natural-language AI Assistant, dual AI engine support (Local/Air-Gapped Ollama or Cloudflare Workers AI), real-time live synchronization, an advanced workload calendar, a collection of 30 3D superhero avatars, and automated CI/CD deployment to Docker Hub and GCP.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.1+-green.svg)
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
- 🏷️ **Statuses & Priorities** - *Not Started* (`status-notstarted`), *In Progress* (`status-inprogress`), *Done* (`status-done`), *Delayed* (`status-delayed`) with High, Medium, Low, None priorities.
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

## 🚀 Quick Start

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

### 🔌 MCP Server (Model Context Protocol for AI Agents)

TeamTasks includes a full-featured **Model Context Protocol (MCP)** server (`mcp_server.py`) and built-in HTTP/SSE endpoints (`/mcp`, `/mcp/sse`), exposing **37 tools**, **9 resources**, and **4 prompts** for complete management of the system by AI Agents.

#### Supported Transports
1. **Stdio Transport (Local IDE / Desktop Agents):**
   ```json
   {
     "mcpServers": {
       "teamtasks": {
         "command": "python",
         "args": ["/path/to/teamtasks/mcp_server.py"]
       }
     }
   }
   ```
2. **Streamable HTTP & SSE Transport (Remote / Containerized Agents):**
   - Streamable HTTP Endpoint: `POST http://localhost:5000/mcp`
   - SSE Endpoint: `GET http://localhost:5000/mcp/sse`
   - Optional authentication via `MCP_API_KEY` in `.env` (`Authorization: Bearer <MCP_API_KEY>`).

#### Available MCP Tools (37 Tools)
- **Tasks (10):** `list_tasks`, `get_task`, `create_task`, `update_task`, `update_task_schedule`, `archive_task`, `unarchive_task`, `delete_task`, `bulk_update_tasks`, `search_tasks`
- **Projects (6):** `list_projects`, `get_project`, `create_project`, `update_project`, `archive_project`, `delete_project`
- **Teams (4):** `list_teams`, `create_team`, `update_team`, `delete_team`
- **Team Members (5):** `list_members`, `create_member`, `update_member`, `delete_member`, `list_avatars`
- **Calendar & Workload (6):** `get_calendar_week`, `get_calendar_month`, `get_member_workload`, `list_special_days`, `create_special_day`, `delete_special_day`
- **Analytics, Diagnostics & Backup (6):** `get_executive_summary`, `get_deadlines_analysis`, `get_stale_and_suggestions`, `get_system_diagnostics`, `export_system_backup`, `restore_system_backup`

You can also view connection snippets and test all 37 MCP tools interactively in the **Admin Panel → שרת MCP (AI Agents)** (`/admin`).

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

#!/usr/bin/env python3
"""
TeamTasks Model Context Protocol (MCP) Server
=============================================
Provides full management of TeamTasks (Tasks, Projects, Teams, Team Members,
Calendar & Workload, Special Days, Analytics, Diagnostics, and Backup/Restore)
for AI Agents (Claude Desktop, Cursor, Antigravity, VS Code Copilot, Windsurf,
and custom MCP clients).

Supported Transports:
1. Stdio (default):
   python mcp_server.py
   python mcp_server.py --transport stdio

2. Streamable HTTP / JSON-RPC (built into Flask app at /mcp, or standalone):
   POST http://localhost:5000/mcp
   python mcp_server.py --transport http --port 8080

3. Server-Sent Events (SSE) (built into Flask app at /mcp/sse & /mcp/messages)

Supported Backend Modes:
- Direct SQLite DB Mode (default when running locally alongside app.py)
- Remote API Proxy Mode (when TEAMTASKS_API_URL environment variable is set)
"""

import os
import sys
import re
import json
import time
import uuid
import queue
import logging
import argparse
from datetime import datetime, date, timedelta
from calendar import monthrange

# Ensure logs never pollute stdout in stdio mode and support UTF-8 on Windows cp1255
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format='[MCP %(levelname)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("teamtasks_mcp")

MCP_SERVER_NAME = "teamtasks-mcp"
MCP_SERVER_VERSION = "1.0.0"
SUPPORTED_PROTOCOL_VERSIONS = ["2025-03-26", "2024-11-05"]
DEFAULT_PROTOCOL_VERSION = "2024-11-05"

# Keep active SSE session queues for /mcp/sse transport
_sse_sessions = {}


_flask_ctx = None


def _get_flask_context():
    """Safely imports Flask app and database models without polluting stdout."""
    global _flask_ctx
    if _flask_ctx is not None:
        return _flask_ctx
    orig_stdout = sys.stdout
    try:
        sys.stdout = sys.stderr
        from app import app, _bump_data_version
        from models import db, Team, TeamMember, Project, Task, SpecialDay, project_teams, member_teams, TaskComment, Subtask
        import ai_tools
        import ai_context
        _flask_ctx = (app, db, Team, TeamMember, Project, Task, SpecialDay, project_teams, member_teams, ai_tools, ai_context, _bump_data_version)
        return _flask_ctx
    finally:
        sys.stdout = orig_stdout


def _notify_db_change(app, _bump_data_version_fn=None):
    """Bumps in-memory version and touches SQLite file mtime so web UI live-syncs immediately."""
    try:
        if _bump_data_version_fn:
            _bump_data_version_fn()
        db_path = os.path.join(app.instance_path, 'tasks.db')
        if not os.path.exists(db_path):
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'tasks.db')
        if os.path.exists(db_path):
            os.utime(db_path, None)
    except Exception as e:
        logger.debug(f"Could not touch db file mtime: {e}")


def _resolve_team(Team, db, team_val):
    """Resolves a Team model instance by ID, English name, or Hebrew name."""
    if team_val is None or str(team_val).strip() == '':
        return None
    if isinstance(team_val, int) or (isinstance(team_val, str) and team_val.strip().isdigit()):
        t = db.session.get(Team, int(str(team_val).strip()))
        if t:
            return t
    clean = str(team_val).strip()
    clean_no_prefix = re.sub(r'^צוות\s+', '', clean).strip()
    t = Team.query.filter(
        (Team.name_he == clean) |
        (Team.name_he == clean_no_prefix) |
        (Team.name_en == clean.lower()) |
        (Team.name_en == clean_no_prefix.lower())
    ).first()
    if t:
        return t
    for candidate in Team.query.all():
        if (clean_no_prefix.lower() in candidate.name_he.lower() or
                clean_no_prefix.lower() in candidate.name_en.lower()):
            return candidate
    return None


def _resolve_member(TeamMember, db, member_val):
    """Resolves a TeamMember model instance by ID, English name, or Hebrew name."""
    if member_val is None or str(member_val).strip() == '':
        return None
    if isinstance(member_val, int) or (isinstance(member_val, str) and member_val.strip().isdigit()):
        m = db.session.get(TeamMember, int(str(member_val).strip()))
        if m:
            return m
    clean = str(member_val).strip()
    m = TeamMember.query.filter(
        (TeamMember.name_he == clean) |
        (TeamMember.name_en == clean.lower())
    ).first()
    if m:
        return m
    for candidate in TeamMember.query.all():
        if clean.lower() in candidate.name_he.lower() or clean.lower() in candidate.name_en.lower():
            return candidate
    return None


def _resolve_target_task(arguments, Task, db, ai_tools):
    """Directly resolves target task without pollution from subtask title or comment content."""
    raw_id = arguments.get("task_id") or arguments.get("id")
    if raw_id is not None:
        try:
            tid = int(raw_id)
            t = db.session.get(Task, tid)
            if t:
                return t
        except (ValueError, TypeError):
            pass
    task_param = arguments.get("task") or arguments.get("task_name")
    if task_param:
        return ai_tools.resolve_task({"task": task_param})
    return None


def _enrich_task_dict(task_obj, members_map=None, teams_map=None):
    """Returns task.to_dict() enriched with Hebrew status, priority, member names, and team name."""
    d = task_obj.to_dict()
    status_he_map = {
        'status-notstarted': 'טרם החל',
        'status-inprogress': 'בתהליך',
        'status-done': 'הושלם',
        'status-delayed': 'מעוכב'
    }
    priority_he_map = {
        'high': 'גבוהה',
        'medium': 'בינונית',
        'low': 'נמוכה',
        'none': 'ללא'
    }
    d['status_he'] = status_he_map.get(d['status'], d['status'])
    d['priority_he'] = priority_he_map.get(d['priority'], d['priority'])
    if members_map is not None:
        d['members_he'] = [members_map.get(m.strip().lower(), m.strip()) for m in d.get('members', []) if m.strip()]
    if teams_map is not None and d.get('team_id'):
        d['team_name_he'] = teams_map.get(d['team_id'], '')
    return d


# ============================================================================
# MCP TOOL DEFINITIONS (JSON Schema)
# ============================================================================

MCP_TOOLS = [
    # --- TASKS ---
    {
        "name": "list_tasks",
        "category": "tasks",
        "title": "רשימת משימות וסינון",
        "description": "List and filter tasks in TeamTasks. Supports filtering by project, team, assigned member (Hebrew or English), status ('status-notstarted', 'status-inprogress', 'status-done', 'status-delayed', or 'not-done' for all open tasks), priority ('high', 'medium', 'low', 'none'), search query, and archive state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Filter by project name or ID"},
                "team": {"type": "string", "description": "Filter by team ID, English name, or Hebrew name"},
                "member": {"type": "string", "description": "Filter by assigned member name (Hebrew or English)"},
                "status": {
                    "type": "string",
                    "description": "Filter by status: 'status-notstarted', 'status-inprogress', 'status-done', 'status-delayed', or 'not-done' (all active/open tasks excluding done)"
                },
                "priority": {
                    "type": "string",
                    "enum": ["high", "medium", "low", "none"],
                    "description": "Filter by priority level"
                },
                "search": {"type": "string", "description": "Search keyword in task title, project, notes, or members"},
                "include_archived": {"type": "boolean", "description": "If true, include both active and archived tasks (default: false)"},
                "archived_only": {"type": "boolean", "description": "If true, return only archived tasks (default: false)"},
                "limit": {"type": "integer", "description": "Maximum number of tasks to return (default: 100)"}
            }
        }
    },
    {
        "name": "get_task",
        "category": "tasks",
        "title": "קבלת פרטי משימה",
        "description": "Get comprehensive details of a specific task by its ID or title/name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Task numeric ID"},
                "task": {"type": "string", "description": "Task title or partial name if ID is unknown"},
                "project": {"type": "string", "description": "Optional project name to disambiguate when searching by title"}
            }
        }
    },
    {
        "name": "create_task",
        "category": "tasks",
        "title": "יצירת משימה חדשה",
        "description": "Create a new task in TeamTasks. Automatically resolves member names (Hebrew or English), status codes, priorities, dates, and project (creates the project if auto_create_project is true).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project name or ID (required)"},
                "task": {"type": "string", "description": "Task title / description (required)"},
                "members": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of assigned team member names (Hebrew or English, e.g. ['אלעד', 'itamar'])"
                },
                "status": {
                    "type": "string",
                    "description": "Initial status: 'status-notstarted' (default), 'status-inprogress', 'status-done', or 'status-delayed'"
                },
                "priority": {
                    "type": "string",
                    "enum": ["high", "medium", "low", "none"],
                    "description": "Task priority: 'high', 'medium', 'low', or 'none' (default)"
                },
                "notes": {"type": "string", "description": "Task notes or detailed instructions"},
                "subtasks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of initial checklist/subtask titles to create with the task"
                },
                "team": {"type": "string", "description": "Optional team ID or name (defaults to project's primary team)"},
                "start_date": {"type": "string", "description": "Scheduled start date (YYYY-MM-DD, DD/MM/YYYY, 'today', 'tomorrow')"},
                "end_date": {"type": "string", "description": "Scheduled target/due date (YYYY-MM-DD, DD/MM/YYYY, 'today', 'tomorrow', 'next week')"},
                "estimated_hours": {"type": "number", "description": "Estimated work hours for workload calculation"},
                "auto_create_project": {"type": "boolean", "description": "Automatically create the project if it does not exist yet (default: true)"}
            },
            "required": ["project", "task"]
        }
    },
    {
        "name": "update_task",
        "category": "tasks",
        "title": "עדכון ועריכת משימה",
        "description": "Update any field of an existing task (title, project, status, priority, members, notes, start/end dates, estimated hours, archive state).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Task ID to update"},
                "task": {"type": "string", "description": "Existing task title (to locate task if ID is omitted) OR new title if ID is provided"},
                "new_title": {"type": "string", "description": "New title for the task"},
                "project": {"type": "string", "description": "Move task to another project (by name or ID)"},
                "status": {
                    "type": "string",
                    "description": "New status ('status-notstarted', 'status-inprogress', 'status-done', 'status-delayed', or Hebrew equivalent)"
                },
                "priority": {
                    "type": "string",
                    "enum": ["high", "medium", "low", "none"],
                    "description": "New priority ('high', 'medium', 'low', 'none')"
                },
                "members": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Replace assigned members with this list of names (Hebrew or English)"
                },
                "add_members": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Add these members to the task without removing existing assignees"
                },
                "remove_members": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Remove these specific members from the task"
                },
                "notes": {"type": "string", "description": "Replace task notes"},
                "append_notes": {"type": "string", "description": "Append text to existing task notes"},
                "add_subtasks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Add new checklist/subtask items to this task"
                },
                "team": {"type": "string", "description": "New team ID or name"},
                "start_date": {"type": "string", "description": "New start date (YYYY-MM-DD, or '' to clear)"},
                "end_date": {"type": "string", "description": "New end/due date (YYYY-MM-DD, or '' to clear)"},
                "estimated_hours": {"type": "number", "description": "New estimated hours"},
                "is_archived": {"type": "boolean", "description": "Set archive state (true/false)"}
            }
        }
    },
    {
        "name": "update_task_schedule",
        "category": "tasks",
        "title": "תזמון ודחיית משימה ביומן",
        "description": "Update task calendar scheduling (start_date, end_date, estimated_hours) or shift dates forward/backward by a number of days.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Task ID"},
                "task": {"type": "string", "description": "Task title if ID is not provided"},
                "start_date": {"type": "string", "description": "New start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "New end date (YYYY-MM-DD)"},
                "shift_days": {"type": "integer", "description": "Shift existing start_date and end_date by N days (positive to postpone, negative to advance)"},
                "estimated_hours": {"type": "number", "description": "Estimated hours for workload capacity"}
            }
        }
    },
    {
        "name": "archive_task",
        "category": "tasks",
        "title": "העברת משימה לארכיון",
        "description": "Move a task to the archive by ID or title.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Task ID"},
                "task": {"type": "string", "description": "Task title if ID is omitted"}
            }
        }
    },
    {
        "name": "unarchive_task",
        "category": "tasks",
        "title": "שחזור משימה מהארכיון",
        "description": "Restore an archived task back to active board (and automatically unarchive its parent project if needed).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Task ID"},
                "task": {"type": "string", "description": "Task title if ID is omitted"}
            }
        }
    },
    {
        "name": "delete_task",
        "category": "tasks",
        "title": "מחיקת משימה",
        "description": "Permanently delete a task from TeamTasks by ID or title.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Task ID to delete"},
                "task": {"type": "string", "description": "Task title if ID is omitted"}
            }
        }
    },
    {
        "name": "bulk_update_tasks",
        "category": "tasks",
        "title": "עדכון משימות מרובות (Batch)",
        "description": "Perform batch updates on multiple tasks at once (update status, priority, project, assign/remove members, archive, unarchive, or delete).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of task IDs to update"
                },
                "status": {"type": "string", "description": "New status to set on all specified tasks"},
                "priority": {"type": "string", "enum": ["high", "medium", "low", "none"], "description": "New priority to set"},
                "project": {"type": "string", "description": "Move all specified tasks to this project"},
                "add_members": {"type": "array", "items": {"type": "string"}, "description": "Add these members to all specified tasks"},
                "remove_members": {"type": "array", "items": {"type": "string"}, "description": "Remove these members from all specified tasks"},
                "is_archived": {"type": "boolean", "description": "Archive (true) or unarchive (false) all specified tasks"},
                "delete": {"type": "boolean", "description": "If true, permanently delete all specified tasks"}
            },
            "required": ["task_ids"]
        }
    },
    {
        "name": "search_tasks",
        "category": "tasks",
        "title": "חיפוש טקסט חופשי במשימות",
        "description": "Full-text search across tasks (matches task title, project name, notes, comments, subtasks, and assigned members).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "include_archived": {"type": "boolean", "description": "Include archived tasks in search results (default: false)"}
            },
            "required": ["query"]
        }
    },

    # --- SUBTASKS / CHECKLIST ---
    {
        "name": "list_subtasks",
        "category": "tasks",
        "title": "רשימת תתי-משימות",
        "description": "List all checklist / subtask items for a specific task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "Task ID"},
                "task": {"type": "string", "description": "Task title if ID is not known"}
            }
        }
    },
    {
        "name": "create_subtask",
        "category": "tasks",
        "title": "הוספת תת-משימה",
        "description": "Add a checklist / subtask item to a task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "Task ID to add subtask to"},
                "task": {"type": "string", "description": "Task title if ID is not known"},
                "title": {"type": "string", "description": "Checklist / subtask item title (required)"},
                "is_completed": {"type": "boolean", "description": "Initial completion status (default: false)"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "update_subtask",
        "category": "tasks",
        "title": "עדכון ועריכת תת-משימה",
        "description": "Update a subtask title, toggle its completion status, or change display order.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Subtask ID (required)"},
                "title": {"type": "string", "description": "New title for the subtask"},
                "is_completed": {"type": "boolean", "description": "Completion state (true for completed, false for pending)"},
                "order": {"type": "integer", "description": "Display order / position"}
            },
            "required": ["id"]
        }
    },
    {
        "name": "delete_subtask",
        "category": "tasks",
        "title": "מחיקת תת-משימה",
        "description": "Permanently delete a subtask / checklist item by its ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Subtask ID to delete (required)"}
            },
            "required": ["id"]
        }
    },

    # --- TASK COMMENTS & NOTES ---
    {
        "name": "list_task_comments",
        "category": "tasks",
        "title": "רשימת הערות ותגובות למשימה",
        "description": "List all comments and notes for a specific task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "Task ID"},
                "task": {"type": "string", "description": "Task title if ID is not known"}
            }
        }
    },
    {
        "name": "create_task_comment",
        "category": "tasks",
        "title": "הוספת הערה/תגובה למשימה",
        "description": "Add a new comment or note to a task. Can associate with a team member or specify custom author name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "Task ID"},
                "task": {"type": "string", "description": "Task title if ID is not known"},
                "content": {"type": "string", "description": "Comment or note content text"},
                "comment": {"type": "string", "description": "Alternative parameter for comment content"},
                "author_name": {"type": "string", "description": "Author name (defaults to resolved member or 'חבר צוות')"},
                "author_avatar": {"type": "string", "description": "Author avatar path or filename (default: default.png)"},
                "member": {"type": "string", "description": "Team member name (Hebrew or English) or member ID to link as author"}
            }
        }
    },
    {
        "name": "delete_task_comment",
        "category": "tasks",
        "title": "מחיקת הערה/תגובה ממשימה",
        "description": "Permanently delete a task comment by its ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Comment ID to delete (required)"}
            },
            "required": ["id"]
        }
    },

    # --- PROJECTS ---
    {
        "name": "list_projects",
        "category": "projects",
        "title": "רשימת פרויקטים",
        "description": "List projects with their assigned teams, task counts, completion percentages, and status breakdown.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["active", "archive", "all"],
                    "description": "Filter by archive mode: 'active' (default), 'archive', or 'all'"
                },
                "team": {"type": "string", "description": "Filter projects belonging to a specific team (ID or name)"}
            }
        }
    },
    {
        "name": "get_project",
        "category": "projects",
        "title": "קבלת פרטי פרויקט ומשימותיו",
        "description": "Get full details of a project by ID or name, including its teams, progress statistics, and all tasks belonging to it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Project ID"},
                "name": {"type": "string", "description": "Project name"}
            }
        }
    },
    {
        "name": "create_project",
        "category": "projects",
        "title": "יצירת פרויקט חדש",
        "description": "Create a new project and associate it with one or more teams.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name (unique)"},
                "teams": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of team names (Hebrew or English) or team IDs to assign the project to"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "update_project",
        "category": "projects",
        "title": "עדכון פרויקט ושיוך צוותים",
        "description": "Rename a project (automatically updating all its tasks) and/or update its assigned teams.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Project ID"},
                "name": {"type": "string", "description": "Current project name (if ID is omitted)"},
                "new_name": {"type": "string", "description": "New name for the project"},
                "teams": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Replace project's assigned teams with this list of team names or IDs"
                },
                "add_teams": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Add these teams to the project without removing existing teams"
                },
                "remove_teams": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Remove these teams from the project"
                }
            }
        }
    },
    {
        "name": "archive_project",
        "category": "projects",
        "title": "ארכוב / שחזור פרויקט",
        "description": "Archive or unarchive an entire project along with all of its tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Project ID"},
                "name": {"type": "string", "description": "Project name"},
                "is_archived": {"type": "boolean", "description": "True to archive, False to restore/unarchive (default: true)"}
            }
        }
    },
    {
        "name": "delete_project",
        "category": "projects",
        "title": "מחיקת פרויקט וכל משימותיו",
        "description": "Permanently delete a project and all tasks associated with it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Project ID"},
                "name": {"type": "string", "description": "Project name"}
            }
        }
    },

    # --- TEAMS ---
    {
        "name": "list_teams",
        "category": "teams",
        "title": "רשימת צוותים וחברים",
        "description": "List all teams in the organization along with their members, project count, and task statistics.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "create_team",
        "category": "teams",
        "title": "יצירת צוות חדש",
        "description": "Create a new team with both English code name and Hebrew display name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_en": {"type": "string", "description": "English identifier (lowercase, e.g. 'devops', 'security')"},
                "name_he": {"type": "string", "description": "Hebrew display name (e.g. 'צוות DevOps', 'אבטחת מידע')"}
            },
            "required": ["name_en", "name_he"]
        }
    },
    {
        "name": "update_team",
        "category": "teams",
        "title": "עדכון פרטי צוות",
        "description": "Update an existing team's Hebrew or English name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Team ID"},
                "name": {"type": "string", "description": "Current team name (Hebrew or English) if ID is omitted"},
                "new_name_en": {"type": "string", "description": "New English name"},
                "new_name_he": {"type": "string", "description": "New Hebrew name"}
            }
        }
    },
    {
        "name": "delete_team",
        "category": "teams",
        "title": "מחיקת צוות",
        "description": "Delete a team by ID or name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Team ID"},
                "name": {"type": "string", "description": "Team name (Hebrew or English)"}
            }
        }
    },

    # --- TEAM MEMBERS ---
    {
        "name": "list_members",
        "category": "members",
        "title": "רשימת חברי צוות",
        "description": "List all team members with their teams, avatar paths, and active/completed task counts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "team": {"type": "string", "description": "Optional team ID or name to filter members"}
            }
        }
    },
    {
        "name": "create_member",
        "category": "members",
        "title": "הוספת חבר צוות חדש",
        "description": "Add a new team member and assign them to one or more teams.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_en": {"type": "string", "description": "English username (lowercase, e.g. 'daniel')"},
                "name_he": {"type": "string", "description": "Hebrew display name (e.g. 'דניאל')"},
                "teams": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of team names (Hebrew/English) or team IDs to assign the member to"
                },
                "avatar_path": {
                    "type": "string",
                    "description": "Avatar filename (e.g. 'avatar_1.png' through 'avatar_48.png', or 'default.png')"
                }
            },
            "required": ["name_en", "name_he"]
        }
    },
    {
        "name": "update_member",
        "category": "members",
        "title": "עדכון חבר צוות",
        "description": "Update a team member's English/Hebrew name, avatar, or team memberships.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Member ID"},
                "name": {"type": "string", "description": "Current member name (Hebrew or English) if ID is omitted"},
                "new_name_en": {"type": "string", "description": "New English username"},
                "new_name_he": {"type": "string", "description": "New Hebrew display name"},
                "teams": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Replace member's teams with this list of team names or IDs"
                },
                "add_teams": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Add member to these additional teams"
                },
                "remove_teams": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Remove member from these teams"
                },
                "avatar_path": {"type": "string", "description": "New avatar filename (e.g. 'avatar_5.png')"}
            }
        }
    },
    {
        "name": "delete_member",
        "category": "members",
        "title": "מחיקת חבר צוות",
        "description": "Delete a team member globally, or remove them from a specific team.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Member ID"},
                "name": {"type": "string", "description": "Member name (Hebrew or English)"},
                "from_team": {"type": "string", "description": "Optional: only remove member from this specific team instead of deleting globally"}
            }
        }
    },
    {
        "name": "list_avatars",
        "category": "members",
        "title": "רשימת אווטארים מובנים",
        "description": "List all predefined 3D avatars available in static/avatars for assigning to team members.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },

    # --- CALENDAR, WORKLOAD & SPECIAL DAYS ---
    {
        "name": "get_calendar_week",
        "category": "calendar",
        "title": "משימות ואירועים שבועיים ביומן",
        "description": "Get scheduled tasks and special days/holidays for a specific week (Sunday to Saturday).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Any date within the target week (YYYY-MM-DD, defaults to today)"},
                "team": {"type": "string", "description": "Optional team ID or name to filter tasks"}
            }
        }
    },
    {
        "name": "get_calendar_month",
        "category": "calendar",
        "title": "משימות ואירועים חודשיים ביומן",
        "description": "Get scheduled tasks and special days/holidays for a specific month.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer", "description": "Year (e.g. 2026, defaults to current year)"},
                "month": {"type": "integer", "description": "Month (1-12, defaults to current month)"},
                "team": {"type": "string", "description": "Optional team ID or name to filter tasks"}
            }
        }
    },
    {
        "name": "get_member_workload",
        "category": "calendar",
        "title": "ניתוח עומס עבודה לחברי צוות",
        "description": "Calculate member workload (assigned tasks, estimated hours, status breakdown) for a date range or overall active tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD). Omit to analyze all active tasks"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD). Omit to analyze all active tasks"},
                "team": {"type": "string", "description": "Optional team ID or name filter"}
            }
        }
    },
    {
        "name": "list_special_days",
        "category": "calendar",
        "title": "רשימת חגים וימים מיוחדים",
        "description": "List special days, holidays, and company events registered in the calendar.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Optional start date filter (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "Optional end date filter (YYYY-MM-DD)"}
            }
        }
    },
    {
        "name": "create_special_day",
        "category": "calendar",
        "title": "הוספת חג / יום מיוחד ליומן",
        "description": "Add a holiday, company event, or special non-working day to the calendar.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date of the event (YYYY-MM-DD or DD/MM/YYYY)"},
                "name": {"type": "string", "description": "Name of the holiday or event"},
                "type": {
                    "type": "string",
                    "enum": ["holiday", "company_event", "other"],
                    "description": "Event type: 'holiday' (default), 'company_event', or 'other'"
                },
                "color": {"type": "string", "description": "Optional hex color code (e.g. '#ef4444')"}
            },
            "required": ["date", "name"]
        }
    },
    {
        "name": "delete_special_day",
        "category": "calendar",
        "title": "מחיקת יום מיוחד מהיומן",
        "description": "Delete a special day / holiday from the calendar by ID, name, or date.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "SpecialDay ID"},
                "name": {"type": "string", "description": "SpecialDay name if ID is omitted"},
                "date": {"type": "string", "description": "SpecialDay date (YYYY-MM-DD) if ID is omitted"}
            }
        }
    },

    # --- ANALYTICS, INSIGHTS & SYSTEM ADMINISTRATION ---
    {
        "name": "get_executive_summary",
        "category": "analytics",
        "title": "דוח מנהלים ותמונת מצב מערכתית",
        "description": "Get an executive summary of the entire system: completion rate, status/priority distribution, per-project progress, and per-member workload.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_deadlines_analysis",
        "category": "analytics",
        "title": "ניתוח דדליינים, איחורים ועיכובים",
        "description": "Identify overdue tasks, tasks due today, tasks due within 7 days, delayed tasks, and active tasks missing target dates.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_stale_and_suggestions",
        "category": "analytics",
        "title": "איתור חוסרים והמלצות לייעול",
        "description": "Find empty projects, unassigned tasks, tasks missing hour estimates, and stuck in-progress tasks requiring attention.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_system_diagnostics",
        "category": "analytics",
        "title": "בדיקת תקינות ומדדי מערכת",
        "description": "Run system diagnostics: SQLite PRAGMA integrity_check, database size, entity counts, uploads stats, and AI engine status.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "export_system_backup",
        "category": "analytics",
        "title": "ייצוא גיבוי נתונים (JSON)",
        "description": "Export full system data or a specific table ('all', 'tasks', 'projects', 'teams', 'members', 'special_days') as a JSON backup object.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "enum": ["all", "tasks", "projects", "teams", "members", "special_days"],
                    "description": "Table to export ('all' exports the entire system with relationships)"
                }
            }
        }
    },
    {
        "name": "restore_system_backup",
        "category": "analytics",
        "title": "שחזור וייבוא נתונים מגיבוי",
        "description": "Restore/upsert records into a specific table ('teams', 'projects', 'members', 'tasks', 'special_days') from a list of JSON records.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "enum": ["teams", "projects", "members", "tasks", "special_days"],
                    "description": "Target table to restore/upsert records into"
                },
                "records": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of record objects to merge/insert"
                }
            },
            "required": ["table_name", "records"]
        }
    },
    {
        "name": "list_database_backups",
        "category": "analytics",
        "title": "רשימת גיבויי מסד נתונים והיסטוריית גרסאות",
        "description": "List all physical SQLite database backup snapshots on the instance mountpoint with dates, sizes, and types (daily automatic 23:00 / manual).",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "create_database_backup",
        "category": "analytics",
        "title": "גיבוי מסד נתונים כעת (Backup Now)",
        "description": "Immediately create a transactionally safe, verified SQLite snapshot of tasks.db to the server backups folder and prune to latest 14 versions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "backup_type": {
                    "type": "string",
                    "enum": ["manual", "daily"],
                    "description": "Type tag for the backup (default 'manual')"
                }
            }
        }
    },
    {
        "name": "restore_database_backup",
        "category": "analytics",
        "title": "שחזור מהיר של מסד הנתונים מגיבוי",
        "description": "Fast restore the database from an existing server-side backup snapshot filename (replaces active tasks.db with verified snapshot).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Filename of the backup snapshot to restore (e.g. tasks_daily_2026-10-31_230000.db)"
                }
            },
            "required": ["filename"]
        }
    }
]


# ============================================================================
# MCP RESOURCES & PROMPTS DEFINITIONS
# ============================================================================

MCP_RESOURCES = [
    {
        "uri": "teamtasks://context/snapshot",
        "name": "TeamTasks Full System Snapshot",
        "description": "Complete real-time snapshot of all teams, members, active projects, active tasks, archived tasks, and special days.",
        "mimeType": "application/json"
    },
    {
        "uri": "teamtasks://analytics/executive-summary",
        "name": "Executive Summary & KPIs",
        "description": "Completion rates, status & priority distributions, project progress, and member workload metrics.",
        "mimeType": "application/json"
    },
    {
        "uri": "teamtasks://analytics/deadlines",
        "name": "Deadlines & Overdue Tasks Analysis",
        "description": "Overdue tasks, tasks due today, tasks due this week, and delayed tasks.",
        "mimeType": "application/json"
    },
    {
        "uri": "teamtasks://analytics/suggestions",
        "name": "System Optimization Suggestions",
        "description": "Empty projects, unassigned tasks, missing hour estimates, and stuck tasks.",
        "mimeType": "application/json"
    },
    {
        "uri": "teamtasks://catalog/teams",
        "name": "Teams & Members Directory",
        "description": "All teams and their assigned members in Hebrew and English.",
        "mimeType": "application/json"
    },
    {
        "uri": "teamtasks://catalog/projects",
        "name": "Projects Catalog",
        "description": "All active and archived projects with team associations.",
        "mimeType": "application/json"
    }
]

MCP_RESOURCE_TEMPLATES = [
    {
        "uriTemplate": "teamtasks://projects/{project_name}",
        "name": "Project Details & Tasks",
        "description": "Detailed view of a specific project and all its tasks by project name or ID.",
        "mimeType": "application/json"
    },
    {
        "uriTemplate": "teamtasks://teams/{team_name}",
        "name": "Team Details, Members & Tasks",
        "description": "Detailed view of a specific team, its members, and assigned tasks.",
        "mimeType": "application/json"
    },
    {
        "uriTemplate": "teamtasks://members/{member_name}",
        "name": "Member Profile & Assigned Tasks",
        "description": "Detailed view of a team member and all tasks assigned to them.",
        "mimeType": "application/json"
    }
]

MCP_PROMPTS = [
    {
        "name": "daily-standup-report",
        "description": "Generate a daily standup report covering tasks in progress, completed tasks, overdue/delayed blockers, and priorities.",
        "arguments": [
            {
                "name": "team",
                "description": "Optional team name (Hebrew or English) to scope the standup report",
                "required": False
            }
        ]
    },
    {
        "name": "sprint-planning-assistant",
        "description": "Analyze unassigned tasks, upcoming deadlines, and member workload capacity to recommend task assignments and scheduling.",
        "arguments": [
            {
                "name": "team",
                "description": "Optional team name to focus sprint planning on",
                "required": False
            }
        ]
    },
    {
        "name": "project-health-audit",
        "description": "Audit a specific project (or all projects) for completion rate, overdue tasks, bottlenecks, and missing estimates.",
        "arguments": [
            {
                "name": "project",
                "description": "Optional project name to audit",
                "required": False
            }
        ]
    },
    {
        "name": "team-workload-balancer",
        "description": "Evaluate workload distribution across team members and suggest concrete task reassignments to prevent bottlenecks.",
        "arguments": []
    }
]


# ============================================================================
# TOOL EXECUTION ENGINE
# ============================================================================

def execute_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """
    Executes an MCP tool by name with the given arguments dictionary.
    Supports both Direct SQLite DB mode and Remote API Proxy mode.
    Returns a dictionary with 'success' (bool) and result data.
    """
    arguments = arguments or {}

    # Check if configured to proxy to a remote TeamTasks server
    remote_url = os.environ.get("TEAMTASKS_API_URL", "").strip().rstrip("/")
    if remote_url and remote_url.lower() not in ("local", "direct"):
        import requests
        headers = {"Content-Type": "application/json"}
        api_key = os.environ.get("MCP_API_KEY", "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        rpc_payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        }
        resp = requests.post(f"{remote_url}/mcp", headers=headers, json=rpc_payload, timeout=30)
        resp.raise_for_status()
        rpc_res = resp.json()
        if "error" in rpc_res:
            return {"success": False, "error": rpc_res["error"].get("message", "Remote MCP error")}
        content_list = rpc_res.get("result", {}).get("content", [])
        if content_list and content_list[0].get("type") == "text":
            try:
                return json.loads(content_list[0]["text"])
            except Exception:
                return {"success": True, "result": content_list[0]["text"]}
        return {"success": True, "result": rpc_res.get("result")}

    app, db, Team, TeamMember, Project, Task, SpecialDay, project_teams, member_teams, ai_tools, ai_context, _bump_data_version = _get_flask_context()

    with app.app_context():
        try:
            from models import TaskComment, Subtask
            db.create_all()
            # Build lookup maps for enriching responses
            all_members = TeamMember.query.all()
            members_map = {m.name_en.strip().lower(): m.name_he.strip() for m in all_members if m.name_en and m.name_he}
            all_teams = Team.query.all()
            teams_map = {t.id: t.name_he for t in all_teams}

            # ----------------------------------------------------------------
            # 1. TASKS TOOLS
            # ----------------------------------------------------------------
            if tool_name == "list_tasks":
                query = Task.query
                if arguments.get("archived_only"):
                    query = query.filter(Task.is_archived == True)
                elif not arguments.get("include_archived"):
                    query = query.filter(Task.is_archived == False)

                # Project filter
                proj_val = arguments.get("project")
                if proj_val:
                    p_obj = ai_tools.resolve_project(proj_val)
                    if p_obj:
                        query = query.filter((Task.project_id == p_obj.id) | (Task.project == p_obj.name))
                    else:
                        query = query.filter(Task.project.ilike(f"%{proj_val.strip()}%"))

                # Team filter
                team_val = arguments.get("team")
                if team_val:
                    t_obj = _resolve_team(Team, db, team_val)
                    if t_obj:
                        team_member_ens = [m.name_en.strip().lower() for m in t_obj.members if m.name_en]
                        team_proj_ids = [p.id for p in t_obj.projects]
                        from sqlalchemy import or_
                        conds = [Task.team_id == t_obj.id]
                        if team_proj_ids:
                            conds.append(Task.project_id.in_(team_proj_ids))
                        for m_en in team_member_ens:
                            conds.append(Task.members.ilike(f"%{m_en}%"))
                        query = query.filter(or_(*conds))

                # Member filter
                member_val = arguments.get("member")
                if member_val:
                    resolved_m = ai_tools.resolve_member_names([member_val])
                    if resolved_m:
                        query = query.filter(Task.members.ilike(f"%{resolved_m[0]}%"))

                # Status filter
                status_val = arguments.get("status")
                if status_val:
                    s_clean = str(status_val).strip().lower()
                    if s_clean in ("not-done", "status-notdone", "open", "פתוח", "פתוחות", "הכל למעט הושלם"):
                        query = query.filter(Task.status != "status-done")
                    else:
                        norm_st = ai_tools.normalize_status(status_val)
                        if norm_st:
                            query = query.filter(Task.status == norm_st)

                # Priority filter
                prio_val = arguments.get("priority")
                if prio_val and str(prio_val).strip().lower() != "all":
                    query = query.filter(Task.priority == str(prio_val).strip().lower())

                # Search keyword filter
                search_val = arguments.get("search")
                if search_val and str(search_val).strip():
                    from sqlalchemy import or_
                    pat = f"%{str(search_val).strip()}%"
                    query = query.filter(or_(
                        Task.task.ilike(pat),
                        Task.project.ilike(pat),
                        Task.notes.ilike(pat),
                        Task.members.ilike(pat)
                    ))

                limit = int(arguments.get("limit") or 100)
                tasks = query.order_by(Task.id.desc()).limit(limit).all()
                enriched = [_enrich_task_dict(t, members_map, teams_map) for t in tasks]
                return {
                    "success": True,
                    "count": len(enriched),
                    "tasks": enriched
                }

            elif tool_name == "get_task":
                task_obj = ai_tools.resolve_task(arguments)
                if not task_obj:
                    return {"success": False, "error": "Task not found. Specify a valid task 'id' or 'task' title."}
                return {
                    "success": True,
                    "task": _enrich_task_dict(task_obj, members_map, teams_map),
                    "summary_he": ai_tools.format_task_status_summary(task_obj, members_lookup=members_map)
                }

            elif tool_name == "create_task":
                proj_val = arguments.get("project") or arguments.get("project_id") or arguments.get("project_name")
                project_obj = None
                if proj_val:
                    project_obj = ai_tools.resolve_project(proj_val)
                    if not project_obj:
                        p_name = str(proj_val).strip()
                        project_obj = Project.query.filter(db.func.lower(Project.name) == p_name.lower()).first()

                # If no project was found or specified, pick an intelligent fallback
                if not project_obj:
                    # 1. By specified team
                    team_obj = _resolve_team(Team, db, arguments.get("team") or arguments.get("team_id"))
                    if team_obj and team_obj.projects:
                        project_obj = [p for p in team_obj.projects if not p.is_archived][0] if any(not p.is_archived for p in team_obj.projects) else team_obj.projects[0]
                    # 2. By specified member
                    elif arguments.get("members"):
                        resolved_m = ai_tools.resolve_member_names(arguments.get("members"))
                        if resolved_m:
                            mem_obj = TeamMember.query.filter(TeamMember.name_en.in_(resolved_m)).first()
                            if mem_obj and mem_obj.teams:
                                for mt in mem_obj.teams:
                                    if mt.projects:
                                        project_obj = [p for p in mt.projects if not p.is_archived][0] if any(not p.is_archived for p in mt.projects) else mt.projects[0]
                                        break
                    # 3. First active project in DB
                    if not project_obj:
                        project_obj = Project.query.filter_by(is_archived=False).first()

                # If still no project exists, create or get 'כללי'
                if not project_obj:
                    p_name = str(proj_val).strip() if proj_val else 'כללי'
                    project_obj = Project.query.filter(db.func.lower(Project.name) == p_name.lower()).first()
                    if not project_obj:
                        team_obj = Team.query.first()
                        project_obj = Project(name=p_name, teams=[team_obj] if team_obj else [])
                        db.session.add(project_obj)
                        db.session.flush()

                title = (arguments.get("task") or arguments.get("title") or arguments.get("task_name") or "").strip()
                if not title:
                    return {"success": False, "error": "'task' title is required."}

                members_resolved = ai_tools.resolve_member_names(arguments.get("members", []))
                status = ai_tools.normalize_status(arguments.get("status")) or "status-notstarted"
                if status not in ("status-notstarted", "status-inprogress", "status-done", "status-delayed"):
                    status = "status-notstarted"

                prio_raw = str(arguments.get("priority") or "none").strip().lower()
                prio_map = {"גבוהה": "high", "בינונית": "medium", "נמוכה": "low", "ללא": "none"}
                priority = prio_map.get(prio_raw, prio_raw)
                if priority not in ("high", "medium", "low", "none"):
                    priority = "none"

                start_date = ai_tools.parse_date_value(arguments.get("start_date") or arguments.get("new_start_date"))
                end_date = ai_tools.parse_date_value(arguments.get("end_date") or arguments.get("new_end_date") or arguments.get("due_date") or arguments.get("target_date"))
                est_hours = arguments.get("estimated_hours")
                if est_hours is not None:
                    try:
                        est_hours = float(est_hours)
                    except (ValueError, TypeError):
                        est_hours = None

                team_id = None
                team_arg = arguments.get("team") or arguments.get("team_id")
                if team_arg:
                    t_obj = _resolve_team(Team, db, team_arg)
                    if t_obj:
                        team_id = t_obj.id
                if not team_id and project_obj.teams:
                    team_id = project_obj.teams[0].id

                new_task = Task(
                    project_id=project_obj.id,
                    project=project_obj.name,
                    task=title,
                    members=",".join(members_resolved),
                    status=status,
                    priority=priority,
                    notes=arguments.get("notes", ""),
                    team_id=team_id,
                    start_date=start_date,
                    end_date=end_date,
                    estimated_hours=est_hours
                )
                db.session.add(new_task)
                db.session.flush()

                # Add initial subtasks / checklist items if provided
                subtasks_input = arguments.get("subtasks")
                if subtasks_input and isinstance(subtasks_input, list):
                    for idx, st_title in enumerate(subtasks_input):
                        st_clean = str(st_title).strip()
                        if st_clean:
                            st_item = Subtask(
                                task_id=new_task.id,
                                title=st_clean,
                                is_completed=False,
                                order=idx + 1
                            )
                            db.session.add(st_item)

                db.session.commit()
                _notify_db_change(app, _bump_data_version)

                return {
                    "success": True,
                    "message": f'נוצרה משימה חדשה #{new_task.id}: "{new_task.task}" בפרויקט "{project_obj.name}"',
                    "task": _enrich_task_dict(new_task, members_map, teams_map)
                }

            elif tool_name == "update_task":
                task_obj = ai_tools.resolve_task(arguments)
                if not task_obj:
                    return {"success": False, "error": "Task to update was not found."}

                if arguments.get("new_title"):
                    task_obj.task = str(arguments["new_title"]).strip()
                elif arguments.get("new_task"):
                    task_obj.task = str(arguments["new_task"]).strip()
                elif arguments.get("task") and arguments.get("id"):
                    task_obj.task = str(arguments["task"]).strip()

                proj_val = arguments.get("project") or arguments.get("project_id")
                if proj_val:
                    p_obj = ai_tools.resolve_project(proj_val)
                    if p_obj:
                        task_obj.project_id = p_obj.id
                        task_obj.project = p_obj.name

                if arguments.get("status"):
                    norm_st = ai_tools.normalize_status(arguments["status"])
                    if norm_st in ("status-notstarted", "status-inprogress", "status-done", "status-delayed"):
                        task_obj.status = norm_st

                if arguments.get("priority"):
                    prio_raw = str(arguments["priority"]).strip().lower()
                    prio_map = {"גבוהה": "high", "בינונית": "medium", "נמוכה": "low", "ללא": "none"}
                    p_val = prio_map.get(prio_raw, prio_raw)
                    if p_val in ("high", "medium", "low", "none"):
                        task_obj.priority = p_val

                if "members" in arguments and arguments["members"] is not None:
                    resolved = ai_tools.resolve_member_names(arguments["members"])
                    task_obj.members = ",".join(resolved)
                else:
                    current_m = [m.strip() for m in (task_obj.members or "").split(",") if m.strip()]
                    add_m_input = arguments.get("add_members") or arguments.get("add_member")
                    if add_m_input:
                        for m in ai_tools.resolve_member_names(add_m_input):
                            if m not in current_m:
                                current_m.append(m)
                    rem_m_input = arguments.get("remove_members") or arguments.get("remove_member")
                    if rem_m_input:
                        to_rem = set(ai_tools.resolve_member_names(rem_m_input))
                        current_m = [m for m in current_m if m not in to_rem]
                    if add_m_input or rem_m_input:
                        task_obj.members = ",".join(current_m)

                if "notes" in arguments and arguments["notes"] is not None:
                    task_obj.notes = str(arguments["notes"])
                elif arguments.get("append_notes"):
                    existing_notes = (task_obj.notes or "").strip()
                    addition = str(arguments["append_notes"]).strip()
                    task_obj.notes = f"{existing_notes}\n{addition}".strip() if existing_notes else addition

                if arguments.get("add_subtasks") and isinstance(arguments["add_subtasks"], list):
                    max_order = db.session.query(db.func.max(Subtask.order)).filter(Subtask.task_id == task_obj.id).scalar() or 0
                    for st_title in arguments["add_subtasks"]:
                        st_clean = str(st_title).strip()
                        if st_clean:
                            max_order += 1
                            st_item = Subtask(
                                task_id=task_obj.id,
                                title=st_clean,
                                is_completed=False,
                                order=max_order
                            )
                            db.session.add(st_item)

                team_arg = arguments.get("team") or arguments.get("team_id")
                if team_arg:
                    t_obj = _resolve_team(Team, db, team_arg)
                    if t_obj:
                        task_obj.team_id = t_obj.id

                start_arg = arguments.get("start_date") or arguments.get("new_start_date")
                if start_arg is not None:
                    task_obj.start_date = ai_tools.parse_date_value(start_arg) if start_arg else None

                end_arg = arguments.get("end_date") or arguments.get("new_end_date") or arguments.get("due_date") or arguments.get("target_date")
                if end_arg is not None:
                    task_obj.end_date = ai_tools.parse_date_value(end_arg) if end_arg else None
                elif start_arg is not None and arguments.get('status') == 'status-delayed':
                    task_obj.end_date = ai_tools.parse_date_value(start_arg)

                if "estimated_hours" in arguments:
                    val = arguments["estimated_hours"]
                    task_obj.estimated_hours = float(val) if val is not None and val != "" else None

                if "is_archived" in arguments and arguments["is_archived"] is not None:
                    task_obj.is_archived = bool(arguments["is_archived"])
                    if not task_obj.is_archived and task_obj.project_id:
                        proj = db.session.get(Project, task_obj.project_id)
                        if proj and proj.is_archived:
                            proj.is_archived = False

                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'עודכנה משימה #{task_obj.id}: "{task_obj.task}"',
                    "task": _enrich_task_dict(task_obj, members_map, teams_map)
                }

            elif tool_name == "update_task_schedule":
                task_obj = ai_tools.resolve_task(arguments)
                if not task_obj:
                    return {"success": False, "error": "Task not found."}

                shift_days = arguments.get("shift_days")
                if shift_days is not None:
                    delta = timedelta(days=int(shift_days))
                    if task_obj.start_date:
                        task_obj.start_date = task_obj.start_date + delta
                    if task_obj.end_date:
                        task_obj.end_date = task_obj.end_date + delta
                    elif not task_obj.end_date:
                        task_obj.end_date = date.today() + delta

                if "start_date" in arguments:
                    task_obj.start_date = ai_tools.parse_date_value(arguments["start_date"]) if arguments["start_date"] else None
                if "end_date" in arguments:
                    task_obj.end_date = ai_tools.parse_date_value(arguments["end_date"]) if arguments["end_date"] else None
                if "estimated_hours" in arguments:
                    val = arguments["estimated_hours"]
                    task_obj.estimated_hours = float(val) if val is not None and val != "" else None

                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'עודכן תזמון משימה #{task_obj.id}: "{task_obj.task}"',
                    "task": _enrich_task_dict(task_obj, members_map, teams_map)
                }

            elif tool_name in ("archive_task", "unarchive_task"):
                task_obj = _resolve_target_task(arguments, Task, db, ai_tools)
                if not task_obj:
                    return {"success": False, "error": "Task not found."}
                is_arch = arguments["is_archived"] if "is_archived" in arguments else (tool_name == "archive_task")
                task_obj.is_archived = bool(is_arch)
                if not is_arch:
                    if task_obj.project_id:
                        proj = db.session.get(Project, task_obj.project_id)
                        if proj and proj.is_archived:
                            proj.is_archived = False
                    elif task_obj.project:
                        proj = Project.query.filter_by(name=task_obj.project).first()
                        if proj and proj.is_archived:
                            proj.is_archived = False
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                action_text = 'הועברה לארכיון' if is_arch else 'שוחזרה מהארכיון'
                return {
                    "success": True,
                    "message": f'משימה #{task_obj.id} "{task_obj.task}" {action_text}',
                    "task": _enrich_task_dict(task_obj, members_map, teams_map)
                }

            elif tool_name == "delete_task":
                task_obj = _resolve_target_task(arguments, Task, db, ai_tools)
                if not task_obj:
                    return {"success": False, "error": "Task not found."}
                task_id = task_obj.id
                title = task_obj.task
                db.session.delete(task_obj)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'נמחקה משימה #{task_id}: "{title}"',
                    "task_id": task_id
                }

            elif tool_name == "bulk_update_tasks":
                task_ids = arguments.get("task_ids") or []
                if not task_ids:
                    return {"success": False, "error": "'task_ids' list is required."}

                updated = []
                deleted_ids = []
                for tid in task_ids:
                    t_obj = db.session.get(Task, int(tid))
                    if not t_obj:
                        continue
                    if arguments.get("delete"):
                        deleted_ids.append(t_obj.id)
                        db.session.delete(t_obj)
                        continue
                    if arguments.get("status"):
                        norm_st = ai_tools.normalize_status(arguments["status"])
                        if norm_st:
                            t_obj.status = norm_st
                    if arguments.get("priority"):
                        t_obj.priority = str(arguments["priority"]).strip().lower()
                    if arguments.get("project"):
                        p_obj = ai_tools.resolve_project(arguments["project"])
                        if p_obj:
                            t_obj.project_id = p_obj.id
                            t_obj.project = p_obj.name
                    if arguments.get("add_members") or arguments.get("remove_members"):
                        cur = [m.strip() for m in (t_obj.members or "").split(",") if m.strip()]
                        if arguments.get("add_members"):
                            for m in ai_tools.resolve_member_names(arguments["add_members"]):
                                if m not in cur:
                                    cur.append(m)
                        if arguments.get("remove_members"):
                            rem = set(ai_tools.resolve_member_names(arguments["remove_members"]))
                            cur = [m for m in cur if m not in rem]
                        t_obj.members = ",".join(cur)
                    if "is_archived" in arguments and arguments["is_archived"] is not None:
                        t_obj.is_archived = bool(arguments["is_archived"])
                    updated.append(t_obj.id)

                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "updated_task_ids": updated,
                    "deleted_task_ids": deleted_ids,
                    "message": f"עודכנו {len(updated)} משימות, נמחקו {len(deleted_ids)} משימות."
                }

            elif tool_name == "search_tasks":
                q = str(arguments.get("query") or "").strip()
                if not q:
                    return {"success": False, "error": "'query' string is required."}
                from sqlalchemy import or_, select
                pat = f"%{q}%"
                sub_query = select(Subtask.task_id).filter(Subtask.title.ilike(pat))
                comm_query = select(TaskComment.task_id).filter(TaskComment.content.ilike(pat))
                query = Task.query.filter(or_(
                    Task.task.ilike(pat),
                    Task.project.ilike(pat),
                    Task.notes.ilike(pat),
                    Task.members.ilike(pat),
                    Task.id.in_(sub_query),
                    Task.id.in_(comm_query)
                ))
                if not arguments.get("include_archived"):
                    query = query.filter(Task.is_archived == False)
                tasks = query.order_by(Task.id.desc()).all()
                return {
                    "success": True,
                    "query": q,
                    "count": len(tasks),
                    "tasks": [_enrich_task_dict(t, members_map, teams_map) for t in tasks]
                }

            # ----------------------------------------------------------------
            # SUBTASKS & CHECKLIST TOOLS
            # ----------------------------------------------------------------
            elif tool_name == "list_subtasks":
                task_obj = _resolve_target_task(arguments, Task, db, ai_tools)
                if not task_obj:
                    return {"success": False, "error": "Task not found. Provide a valid task ID or title."}
                subtasks = Subtask.query.filter_by(task_id=task_obj.id).order_by(Subtask.order.asc(), Subtask.id.asc()).all()
                return {
                    "success": True,
                    "task_id": task_obj.id,
                    "task_title": task_obj.task,
                    "count": len(subtasks),
                    "completed_count": sum(1 for s in subtasks if s.is_completed),
                    "subtasks": [s.to_dict() for s in subtasks]
                }

            elif tool_name == "create_subtask":
                task_obj = _resolve_target_task(arguments, Task, db, ai_tools)
                if not task_obj:
                    return {"success": False, "error": "Task not found. Provide a valid task ID or title."}
                title = str(arguments.get("title") or "").strip()
                if not title:
                    return {"success": False, "error": "'title' is required for subtask."}
                max_order = db.session.query(db.func.max(Subtask.order)).filter(Subtask.task_id == task_obj.id).scalar() or 0
                new_st = Subtask(
                    task_id=task_obj.id,
                    title=title,
                    is_completed=bool(arguments.get("is_completed", False)),
                    order=max_order + 1
                )
                db.session.add(new_st)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'נוספה תת-משימה "{new_st.title}" למשימה #{task_obj.id}',
                    "subtask": new_st.to_dict(),
                    "task": _enrich_task_dict(task_obj, members_map, teams_map)
                }

            elif tool_name == "update_subtask":
                st_id = arguments.get("id")
                if not st_id:
                    return {"success": False, "error": "'id' is required to update subtask."}
                subtask = db.session.get(Subtask, int(st_id))
                if not subtask:
                    return {"success": False, "error": f"Subtask #{st_id} not found."}
                if "title" in arguments and str(arguments["title"]).strip():
                    subtask.title = str(arguments["title"]).strip()
                if "is_completed" in arguments and arguments["is_completed"] is not None:
                    subtask.is_completed = bool(arguments["is_completed"])
                if "order" in arguments and arguments["order"] is not None:
                    try:
                        subtask.order = int(arguments["order"])
                    except (ValueError, TypeError):
                        pass
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                task_obj = db.session.get(Task, subtask.task_id)
                return {
                    "success": True,
                    "message": f'עודכנה תת-משימה #{subtask.id}: "{subtask.title}" (הושלם: {subtask.is_completed})',
                    "subtask": subtask.to_dict(),
                    "task": _enrich_task_dict(task_obj, members_map, teams_map) if task_obj else None
                }

            elif tool_name == "delete_subtask":
                st_id = arguments.get("id")
                if not st_id:
                    return {"success": False, "error": "'id' is required to delete subtask."}
                subtask = db.session.get(Subtask, int(st_id))
                if not subtask:
                    return {"success": False, "error": f"Subtask #{st_id} not found."}
                t_id = subtask.task_id
                title = subtask.title
                db.session.delete(subtask)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                task_obj = db.session.get(Task, t_id)
                return {
                    "success": True,
                    "message": f'נמחקה תת-משימה #{st_id}: "{title}"',
                    "task": _enrich_task_dict(task_obj, members_map, teams_map) if task_obj else None
                }

            # ----------------------------------------------------------------
            # TASK COMMENTS & NOTES TOOLS
            # ----------------------------------------------------------------
            elif tool_name == "list_task_comments":
                task_obj = _resolve_target_task(arguments, Task, db, ai_tools)
                if not task_obj:
                    return {"success": False, "error": "Task not found. Provide a valid task ID or title."}
                comments = TaskComment.query.filter_by(task_id=task_obj.id).order_by(TaskComment.created_at.asc()).all()
                return {
                    "success": True,
                    "task_id": task_obj.id,
                    "task_title": task_obj.task,
                    "count": len(comments),
                    "comments": [c.to_dict() for c in comments]
                }

            elif tool_name == "create_task_comment":
                task_obj = _resolve_target_task(arguments, Task, db, ai_tools)
                if not task_obj:
                    return {"success": False, "error": "Task not found. Provide a valid task ID or title."}
                content = str(arguments.get("content") or arguments.get("comment") or "").strip()
                if not content:
                    return {"success": False, "error": "'content' (or 'comment') is required for comment."}

                author_name = str(arguments.get("author_name") or "").strip()
                author_avatar = str(arguments.get("author_avatar") or "").strip()
                member_val = arguments.get("member") or arguments.get("member_id")
                m_obj = None
                if member_val:
                    m_obj = _resolve_member(TeamMember, db, member_val)
                if m_obj:
                    if not author_name:
                        author_name = m_obj.name_he
                    if not author_avatar or author_avatar == "default.png":
                        author_avatar = m_obj.avatar_path or "default.png"

                if not author_name:
                    author_name = "חבר צוות"
                if not author_avatar:
                    author_avatar = "default.png"

                new_comment = TaskComment(
                    task_id=task_obj.id,
                    author_name=author_name,
                    author_avatar=author_avatar,
                    member_id=m_obj.id if m_obj else None,
                    content=content
                )
                db.session.add(new_comment)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'נוספה הערה למשימה #{task_obj.id} מאת {author_name}',
                    "comment": new_comment.to_dict(),
                    "task": _enrich_task_dict(task_obj, members_map, teams_map)
                }

            elif tool_name == "delete_task_comment":
                c_id = arguments.get("id")
                if not c_id:
                    return {"success": False, "error": "'id' is required to delete comment."}
                comment = db.session.get(TaskComment, int(c_id))
                if not comment:
                    return {"success": False, "error": f"Comment #{c_id} not found."}
                t_id = comment.task_id
                db.session.delete(comment)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                task_obj = db.session.get(Task, t_id)
                return {
                    "success": True,
                    "message": f"נמחקה תגובה #{c_id} ממשימה #{t_id}",
                    "task": _enrich_task_dict(task_obj, members_map, teams_map) if task_obj else None
                }

            # ----------------------------------------------------------------
            # 2. PROJECTS TOOLS
            # ----------------------------------------------------------------
            elif tool_name == "list_projects":
                mode = arguments.get("mode", "active")
                query = Project.query
                if mode == "archive":
                    query = query.filter(Project.is_archived == True)
                elif mode != "all":
                    query = query.filter(Project.is_archived == False)

                team_val = arguments.get("team")
                if team_val:
                    t_obj = _resolve_team(Team, db, team_val)
                    if t_obj:
                        query = query.filter(Project.teams.any(Team.id == t_obj.id))

                projects = query.order_by(Project.name).all()
                results = []
                for p in projects:
                    p_dict = p.to_dict()
                    p_tasks = [t for t in p.tasks if (t.is_archived if mode == "archive" else not t.is_archived)]
                    done_cnt = sum(1 for t in p_tasks if t.status == "status-done")
                    inprog_cnt = sum(1 for t in p_tasks if t.status == "status-inprogress")
                    delayed_cnt = sum(1 for t in p_tasks if t.status == "status-delayed")
                    notstarted_cnt = sum(1 for t in p_tasks if t.status == "status-notstarted")
                    p_dict["task_counts"] = {
                        "total": len(p_tasks),
                        "done": done_cnt,
                        "in_progress": inprog_cnt,
                        "delayed": delayed_cnt,
                        "not_started": notstarted_cnt,
                        "completion_rate": round(done_cnt / len(p_tasks) * 100, 1) if p_tasks else 0.0
                    }
                    results.append(p_dict)
                return {
                    "success": True,
                    "count": len(results),
                    "projects": results
                }

            elif tool_name == "get_project":
                proj_val = arguments.get("id") or arguments.get("name")
                p_obj = ai_tools.resolve_project(proj_val)
                if not p_obj:
                    return {"success": False, "error": "Project not found."}
                p_dict = p_obj.to_dict()
                p_tasks = [_enrich_task_dict(t, members_map, teams_map) for t in p_obj.tasks]
                active_tasks = [t for t in p_tasks if not t["is_archived"]]
                done_cnt = sum(1 for t in active_tasks if t["status"] == "status-done")
                p_dict["active_task_count"] = len(active_tasks)
                p_dict["completion_rate"] = round(done_cnt / len(active_tasks) * 100, 1) if active_tasks else 0.0
                p_dict["tasks"] = p_tasks
                return {
                    "success": True,
                    "project": p_dict
                }

            elif tool_name == "create_project":
                name = (arguments.get('name') or arguments.get('name_he') or arguments.get('project_name') or arguments.get('title') or '').strip()
                if not name:
                    return {"success": False, "error": "שם פרויקט הוא שדה חובה"}

                existing = Project.query.filter_by(name=name).first()
                if existing:
                    return {"success": False, "error": f'פרויקט בשם "{name}" כבר קיים'}

                teams_to_add = []
                teams_input = arguments.get('teams') or arguments.get('team') or arguments.get('team_name') or arguments.get('team_ids')
                if teams_input:
                    raw_list = teams_input if isinstance(teams_input, list) else [teams_input]
                    for tv in raw_list:
                        t_obj = _resolve_team(Team, db, tv)
                        if t_obj and t_obj not in teams_to_add:
                            teams_to_add.append(t_obj)

                if not teams_to_add:
                    first_team = Team.query.first()
                    if first_team:
                        teams_to_add.append(first_team)

                project = Project(name=name, teams=teams_to_add)
                db.session.add(project)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                teams_str = ', '.join([t.name_he for t in project.teams])
                return {
                    "success": True,
                    "message": f'נוצר פרויקט חדש: "{project.name}" (צוותים: {teams_str})',
                    "project": project.to_dict(),
                    "project_id": project.id
                }

            elif tool_name == "update_project":
                proj_val = arguments.get("id") or arguments.get("name") or arguments.get("project_id") or arguments.get("project") or arguments.get("old_name")
                p_obj = ai_tools.resolve_project(proj_val)
                if not p_obj:
                    return {"success": False, "error": "Project not found."}

                new_name = (arguments.get("new_name") or "").strip()
                if not new_name and "name" in arguments and proj_val and str(arguments.get("name")).strip() != p_obj.name:
                    new_name = str(arguments.get("name")).strip()

                if new_name and new_name != p_obj.name:
                    existing = Project.query.filter_by(name=new_name).first()
                    if existing and existing.id != p_obj.id:
                        return {"success": False, "error": f'פרויקט בשם "{new_name}" כבר קיים.'}
                    old_name = p_obj.name
                    p_obj.name = new_name
                    for t in Task.query.filter((Task.project_id == p_obj.id) | (Task.project == old_name)).all():
                        t.project = new_name
                        t.project_id = p_obj.id

                teams_input = arguments.get("teams") or arguments.get("team") or arguments.get("team_name") or arguments.get("team_ids")
                if teams_input is not None:
                    raw_list = teams_input if isinstance(teams_input, list) else [teams_input]
                    new_teams = []
                    for tv in raw_list:
                        t_obj = _resolve_team(Team, db, tv)
                        if t_obj and t_obj not in new_teams:
                            new_teams.append(t_obj)
                    is_add = arguments.get("add_team", True) or ("teams" not in arguments and "team_ids" not in arguments)
                    if is_add:
                        for t in new_teams:
                            if t not in p_obj.teams:
                                p_obj.teams.append(t)
                    else:
                        p_obj.teams = new_teams
                else:
                    if arguments.get("add_teams") or arguments.get("add_team"):
                        add_items = arguments.get("add_teams") or arguments.get("add_team")
                        raw_list = add_items if isinstance(add_items, list) else [add_items]
                        for tv in raw_list:
                            t_obj = _resolve_team(Team, db, tv)
                            if t_obj and t_obj not in p_obj.teams:
                                p_obj.teams.append(t_obj)
                    if arguments.get("remove_teams") or arguments.get("remove_team"):
                        rem_items = arguments.get("remove_teams") or arguments.get("remove_team")
                        raw_list = rem_items if isinstance(rem_items, list) else [rem_items]
                        for tv in raw_list:
                            t_obj = _resolve_team(Team, db, tv)
                            if t_obj and t_obj in p_obj.teams and len(p_obj.teams) > 1:
                                p_obj.teams.remove(t_obj)

                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                teams_str = ', '.join([t.name_he for t in p_obj.teams])
                return {
                    "success": True,
                    "message": f'עודכן פרויקט "{p_obj.name}" (צוותים: {teams_str})',
                    "project": p_obj.to_dict()
                }

            elif tool_name in ("archive_project", "unarchive_project"):
                proj_val = arguments.get("id") or arguments.get("name") or arguments.get("project_id") or arguments.get("project")
                project = ai_tools.resolve_project(proj_val)
                if not project:
                    return {"success": False, "error": "פרויקט לא נמצא"}
                is_arch = arguments.get("is_archived", True) if tool_name == "archive_project" else False
                if "is_archived" in arguments:
                    is_arch = bool(arguments["is_archived"])
                project.is_archived = is_arch
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                action_text = 'הועבר לארכיון' if is_arch else 'שוחזר מהארכיון'
                return {
                    "success": True,
                    "message": f'פרויקט "{project.name}" {action_text}',
                    "project": project.to_dict()
                }

            elif tool_name == "delete_project":
                proj_val = arguments.get("id") or arguments.get("name") or arguments.get("project_id") or arguments.get("project")
                project = ai_tools.resolve_project(proj_val)
                if not project:
                    return {"success": False, "error": "פרויקט למחיקה לא נמצא"}
                p_name = project.name
                db.session.delete(project)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'נמחק פרויקט: "{p_name}"'
                }

            # ----------------------------------------------------------------
            # 3. TEAMS TOOLS
            # ----------------------------------------------------------------
            elif tool_name == "list_teams":
                teams = Team.query.all()
                results = []
                for t in teams:
                    td = t.to_dict()
                    td["project_count"] = len([p for p in t.projects if not p.is_archived])
                    td["projects"] = [p.name for p in t.projects if not p.is_archived]
                    results.append(td)
                return {
                    "success": True,
                    "count": len(results),
                    "teams": results
                }

            elif tool_name == "create_team":
                name_en = (arguments.get('name_en') or arguments.get('name') or '').strip().lower()
                name_he = (arguments.get('name_he') or arguments.get('name') or '').strip()
                if not name_en or not name_he:
                    return {"success": False, "error": "שם צוות באנגלית ובעברית הם שדות חובה"}

                existing = Team.query.filter((Team.name_en == name_en) | (Team.name_he == name_he)).first()
                if existing:
                    return {"success": False, "error": f'צוות עם שם זה כבר קיים ({name_he} / {name_en})'}

                team = Team(name_en=name_en, name_he=name_he)
                db.session.add(team)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'נוצר צוות חדש: "{team.name_he}" ({team.name_en})',
                    "team": team.to_dict(),
                    "team_id": team.id
                }

            elif tool_name == "update_team":
                t_obj = _resolve_team(Team, db, arguments.get("id") or arguments.get("name"))
                if not t_obj:
                    return {"success": False, "error": "Team not found."}
                if arguments.get("new_name_en"):
                    t_obj.name_en = str(arguments["new_name_en"]).strip().lower()
                if arguments.get("new_name_he"):
                    t_obj.name_he = str(arguments["new_name_he"]).strip()
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'עודכן צוות "{t_obj.name_he}" ({t_obj.name_en})',
                    "team": t_obj.to_dict()
                }

            elif tool_name == "delete_team":
                t_obj = _resolve_team(Team, db, arguments.get("id") or arguments.get("name"))
                if not t_obj:
                    return {"success": False, "error": "Team not found."}
                name_he = t_obj.name_he
                db.session.delete(t_obj)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'נמחק צוות "{name_he}"'
                }

            # ----------------------------------------------------------------
            # 4. MEMBERS TOOLS
            # ----------------------------------------------------------------
            elif tool_name == "list_members":
                team_val = arguments.get("team")
                if team_val:
                    t_obj = _resolve_team(Team, db, team_val)
                    members = list(t_obj.members) if t_obj else []
                else:
                    members = TeamMember.query.order_by(TeamMember.name_he).all()

                active_tasks = Task.query.filter_by(is_archived=False).all()
                results = []
                for m in members:
                    md = m.to_dict()
                    m_en = (m.name_en or "").strip().lower()
                    m_tasks = [t for t in active_tasks if m_en in [x.strip().lower() for x in (t.members or "").split(",") if x.strip()]]
                    md["task_counts"] = {
                        "total_active": len(m_tasks),
                        "open": sum(1 for t in m_tasks if t.status != "status-done"),
                        "done": sum(1 for t in m_tasks if t.status == "status-done"),
                        "in_progress": sum(1 for t in m_tasks if t.status == "status-inprogress"),
                        "estimated_hours": sum(t.estimated_hours or 0.0 for t in m_tasks if t.status != "status-done")
                    }
                    results.append(md)
                return {
                    "success": True,
                    "count": len(results),
                    "members": results
                }

            elif tool_name == "create_member":
                name_en = str(arguments.get("name_en") or "").strip().lower()
                name_he = str(arguments.get("name_he") or "").strip()
                if not name_en or not name_he:
                    return {"success": False, "error": "Both 'name_en' and 'name_he' are required."}

                teams_list = []
                for tv in (arguments.get("teams") or []):
                    t_obj = _resolve_team(Team, db, tv)
                    if t_obj and t_obj not in teams_list:
                        teams_list.append(t_obj)
                if not teams_list:
                    first_t = Team.query.first()
                    if first_t:
                        teams_list.append(first_t)

                avatar_path = str(arguments.get("avatar_path") or "default.png").strip()
                member = TeamMember(
                    team_id=teams_list[0].id if teams_list else None,
                    name_en=name_en,
                    name_he=name_he,
                    avatar_path=avatar_path
                )
                for t_obj in teams_list:
                    member.teams.append(t_obj)

                db.session.add(member)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'נוסף חבר צוות חדש: "{name_he}" ({name_en})',
                    "member": member.to_dict()
                }

            elif tool_name == "update_member":
                m_obj = _resolve_member(TeamMember, db, arguments.get("id") or arguments.get("name"))
                if not m_obj:
                    return {"success": False, "error": "Team member not found."}

                old_en = m_obj.name_en.strip().lower()
                if arguments.get("new_name_en"):
                    new_en = str(arguments["new_name_en"]).strip().lower()
                    m_obj.name_en = new_en
                    # Update references in tasks
                    for t in Task.query.filter(Task.members.ilike(f"%{old_en}%")).all():
                        parts = [x.strip() for x in (t.members or "").split(",") if x.strip()]
                        parts = [new_en if x.lower() == old_en else x for x in parts]
                        t.members = ",".join(parts)

                if arguments.get("new_name_he"):
                    m_obj.name_he = str(arguments["new_name_he"]).strip()

                if arguments.get("avatar_path"):
                    m_obj.avatar_path = str(arguments["avatar_path"]).strip()

                if "teams" in arguments and arguments["teams"] is not None:
                    new_teams = []
                    for tv in arguments["teams"]:
                        t_obj = _resolve_team(Team, db, tv)
                        if t_obj and t_obj not in new_teams:
                            new_teams.append(t_obj)
                    if new_teams:
                        m_obj.teams = new_teams
                        m_obj.team_id = new_teams[0].id
                else:
                    if arguments.get("add_teams"):
                        for tv in arguments["add_teams"]:
                            t_obj = _resolve_team(Team, db, tv)
                            if t_obj and t_obj not in m_obj.teams:
                                m_obj.teams.append(t_obj)
                    if arguments.get("remove_teams"):
                        for tv in arguments["remove_teams"]:
                            t_obj = _resolve_team(Team, db, tv)
                            if t_obj and t_obj in m_obj.teams and len(m_obj.teams) > 1:
                                m_obj.teams.remove(t_obj)
                    if m_obj.teams:
                        m_obj.team_id = m_obj.teams[0].id

                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'עודכן חבר צוות "{m_obj.name_he}" ({m_obj.name_en})',
                    "member": m_obj.to_dict()
                }

            elif tool_name == "delete_member":
                m_obj = _resolve_member(TeamMember, db, arguments.get("id") or arguments.get("name"))
                if not m_obj:
                    return {"success": False, "error": "Team member not found."}

                from_team_val = arguments.get("from_team")
                if from_team_val:
                    t_obj = _resolve_team(Team, db, from_team_val)
                    if t_obj and t_obj in m_obj.teams:
                        m_obj.teams.remove(t_obj)
                        if len(m_obj.teams) == 0:
                            db.session.delete(m_obj)
                        else:
                            m_obj.team_id = m_obj.teams[0].id
                        db.session.commit()
                        _notify_db_change(app, _bump_data_version)
                        return {
                            "success": True,
                            "message": f'חבר הצוות "{m_obj.name_he}" הוסר מצוות "{t_obj.name_he}"'
                        }

                name_he = m_obj.name_he
                db.session.delete(m_obj)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'נמחק חבר צוות "{name_he}"'
                }

            elif tool_name == "list_avatars":
                base_dir = os.path.abspath(os.path.dirname(__file__))
                avatar_dir = os.path.join(base_dir, "static", "avatars")
                avatars = []
                if os.path.exists(avatar_dir):
                    files = [f for f in os.listdir(avatar_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg'))]
                    files.sort(key=lambda n: int(re.findall(r'\d+', n)[0]) if re.findall(r'\d+', n) else 999)
                    avatars = [{"filename": f, "url": f"/static/avatars/{f}"} for f in files]
                return {
                    "success": True,
                    "count": len(avatars),
                    "avatars": avatars
                }

            # ----------------------------------------------------------------
            # 5. CALENDAR, WORKLOAD & SPECIAL DAYS TOOLS
            # ----------------------------------------------------------------
            elif tool_name == "get_calendar_week":
                ref_date = ai_tools.parse_date_value(arguments.get("date")) or date.today()
                days_since_sunday = (ref_date.weekday() + 1) % 7
                week_start = ref_date - timedelta(days=days_since_sunday)
                week_end = week_start + timedelta(days=6)

                from sqlalchemy import or_, and_
                query = Task.query.filter(
                    Task.is_archived == False,
                    or_(
                        Task.start_date.between(week_start, week_end),
                        Task.end_date.between(week_start, week_end),
                        and_(Task.start_date <= week_start, Task.end_date >= week_end)
                    )
                )
                if arguments.get("team"):
                    t_obj = _resolve_team(Team, db, arguments["team"])
                    if t_obj:
                        m_names = [m.name_en for m in t_obj.members if m.name_en]
                        m_filters = [Task.members.contains(n) for n in m_names]
                        query = query.filter(or_(Task.team_id == t_obj.id, *m_filters))

                tasks = query.all()
                special_days = SpecialDay.query.filter(SpecialDay.date.between(week_start, week_end)).order_by(SpecialDay.date).all()
                return {
                    "success": True,
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "task_count": len(tasks),
                    "tasks": [_enrich_task_dict(t, members_map, teams_map) for t in tasks],
                    "special_days": [sd.to_dict() for sd in special_days]
                }

            elif tool_name == "get_calendar_month":
                now = date.today()
                year = int(arguments.get("year") or now.year)
                month = int(arguments.get("month") or now.month)
                month = max(1, min(12, month))
                month_start = date(year, month, 1)
                month_end = date(year, month, monthrange(year, month)[1])

                from sqlalchemy import or_, and_
                query = Task.query.filter(
                    Task.is_archived == False,
                    or_(
                        Task.start_date.between(month_start, month_end),
                        Task.end_date.between(month_start, month_end),
                        and_(Task.start_date <= month_start, Task.end_date >= month_end)
                    )
                )
                if arguments.get("team"):
                    t_obj = _resolve_team(Team, db, arguments["team"])
                    if t_obj:
                        m_names = [m.name_en for m in t_obj.members if m.name_en]
                        m_filters = [Task.members.contains(n) for n in m_names]
                        query = query.filter(or_(Task.team_id == t_obj.id, *m_filters))

                tasks = query.all()
                special_days = SpecialDay.query.filter(SpecialDay.date.between(month_start, month_end)).order_by(SpecialDay.date).all()
                return {
                    "success": True,
                    "year": year,
                    "month": month,
                    "month_start": month_start.isoformat(),
                    "month_end": month_end.isoformat(),
                    "task_count": len(tasks),
                    "tasks": [_enrich_task_dict(t, members_map, teams_map) for t in tasks],
                    "special_days": [sd.to_dict() for sd in special_days]
                }

            elif tool_name == "get_member_workload":
                start_d = ai_tools.parse_date_value(arguments.get("start_date"))
                end_d = ai_tools.parse_date_value(arguments.get("end_date"))
                query = Task.query.filter(Task.is_archived == False)

                if start_d and end_d:
                    from sqlalchemy import or_, and_
                    query = query.filter(or_(
                        Task.start_date.between(start_d, end_d),
                        Task.end_date.between(start_d, end_d),
                        and_(Task.start_date <= start_d, Task.end_date >= end_d)
                    ))

                t_obj = _resolve_team(Team, db, arguments.get("team")) if arguments.get("team") else None
                members = list(t_obj.members) if t_obj else TeamMember.query.order_by(TeamMember.name_he).all()
                tasks = query.all()

                workload_list = []
                for m in members:
                    m_en = (m.name_en or "").strip().lower()
                    m_tasks = [
                        _enrich_task_dict(t, members_map, teams_map)
                        for t in tasks
                        if m_en and m_en in [n.strip().lower() for n in (t.members or "").split(",") if n.strip()]
                    ]
                    open_tasks = [t for t in m_tasks if t["status"] != "status-done"]
                    total_hours = sum(t.get("estimated_hours") or 0.0 for t in open_tasks)
                    workload_list.append({
                        "member": m.to_dict(),
                        "total_tasks": len(m_tasks),
                        "open_tasks_count": len(open_tasks),
                        "done_tasks_count": len(m_tasks) - len(open_tasks),
                        "total_estimated_hours": round(total_hours, 1),
                        "tasks": m_tasks
                    })
                return {
                    "success": True,
                    "start_date": start_d.isoformat() if start_d else None,
                    "end_date": end_d.isoformat() if end_d else None,
                    "workload": workload_list
                }

            elif tool_name == "list_special_days":
                query = SpecialDay.query
                start_d = ai_tools.parse_date_value(arguments.get("start_date"))
                end_d = ai_tools.parse_date_value(arguments.get("end_date"))
                if start_d and end_d:
                    query = query.filter(SpecialDay.date.between(start_d, end_d))
                elif start_d:
                    query = query.filter(SpecialDay.date >= start_d)
                days = query.order_by(SpecialDay.date).all()
                return {
                    "success": True,
                    "count": len(days),
                    "special_days": [d.to_dict() for d in days]
                }

            elif tool_name == "create_special_day":
                date_val = ai_tools.parse_date_value(arguments.get('date'))
                if not date_val:
                    return {"success": False, "error": "תאריך לא תקין או חסר"}

                name = (arguments.get('name') or arguments.get('title') or arguments.get('description') or 'יום מיוחד').strip()
                day_type = (arguments.get('type') or 'holiday').strip().lower()

                existing = SpecialDay.query.filter_by(date=date_val).first()
                if existing:
                    existing.name = name
                    existing.type = day_type
                    existing.description = arguments.get('description', '')
                    db.session.commit()
                    _notify_db_change(app, _bump_data_version)
                    return {
                        "success": True,
                        "message": f'עודכן יום מיוחד: {name} בתאריך {date_val.strftime("%d/%m/%Y")}',
                        "special_day": existing.to_dict(),
                        "special_day_id": existing.id
                    }

                sd = SpecialDay(
                    date=date_val,
                    name=name,
                    type=day_type,
                    description=arguments.get('description', '')
                )
                db.session.add(sd)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'נוסף יום מיוחד: {name} בתאריך {date_val.strftime("%d/%m/%Y")}',
                    "special_day": sd.to_dict(),
                    "special_day_id": sd.id
                }

            elif tool_name == "delete_special_day":
                sd = None
                if arguments.get("id"):
                    sd = db.session.get(SpecialDay, int(arguments["id"]))
                elif arguments.get("date"):
                    d_val = ai_tools.parse_date_value(arguments["date"])
                    if d_val:
                        sd = SpecialDay.query.filter_by(date=d_val).first()
                elif arguments.get("name"):
                    sd = SpecialDay.query.filter(SpecialDay.name.ilike(f"%{arguments['name'].strip()}%")).first()

                if not sd:
                    return {"success": False, "error": "Special day not found."}
                name = sd.name
                db.session.delete(sd)
                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": f'נמחק יום מיוחד: "{name}"'
                }

            # ----------------------------------------------------------------
            # 6. ANALYTICS, DIAGNOSTICS & BACKUP TOOLS
            # ----------------------------------------------------------------
            elif tool_name == "get_executive_summary":
                return {
                    "success": True,
                    "summary": ai_context.get_executive_summary()
                }

            elif tool_name == "get_deadlines_analysis":
                return {
                    "success": True,
                    "deadlines": ai_context.get_deadlines_analysis()
                }

            elif tool_name == "get_stale_and_suggestions":
                return {
                    "success": True,
                    "suggestions": ai_context.get_stale_and_suggestions()
                }

            elif tool_name == "get_system_diagnostics":
                from sqlalchemy import text
                from ai_service import ai_service
                integrity_res = db.session.execute(text("PRAGMA integrity_check")).fetchone()
                integrity = integrity_res[0] if integrity_res else "unknown"
                db_path = os.path.join(app.instance_path, "tasks.db")
                db_size_kb = round(os.path.getsize(db_path) / 1024, 1) if os.path.exists(db_path) else 0

                return {
                    "success": True,
                    "diagnostics": {
                        "db_integrity": integrity,
                        "db_size_kb": db_size_kb,
                        "counts": {
                            "teams": Team.query.count(),
                            "members": TeamMember.query.count(),
                            "projects_active": Project.query.filter_by(is_archived=False).count(),
                            "projects_archived": Project.query.filter_by(is_archived=True).count(),
                            "tasks_active": Task.query.filter_by(is_archived=False).count(),
                            "tasks_archived": Task.query.filter_by(is_archived=True).count(),
                            "special_days": SpecialDay.query.count()
                        },
                        "ai_status": ai_service.get_status(),
                        "mcp_server": {
                            "name": MCP_SERVER_NAME,
                            "version": MCP_SERVER_VERSION,
                            "tools_count": len(MCP_TOOLS)
                        }
                    }
                }

            elif tool_name == "export_system_backup":
                table_name = arguments.get("table_name", "all")
                models_map = {
                    "teams": Team,
                    "projects": Project,
                    "members": TeamMember,
                    "tasks": Task,
                    "special_days": SpecialDay,
                    "subtasks": Subtask,
                    "task_comments": TaskComment
                }
                if table_name == "all":
                    full_data = {name: [r.to_dict() for r in model.query.all()] for name, model in models_map.items()}
                    pt_rows = db.session.execute(project_teams.select()).fetchall()
                    full_data["project_teams"] = [{"project_id": r[0], "team_id": r[1]} for r in pt_rows]
                    mt_rows = db.session.execute(member_teams.select()).fetchall()
                    full_data["member_teams"] = [{"member_id": r[0], "team_id": r[1]} for r in mt_rows]
                    return {
                        "success": True,
                        "table": "all",
                        "timestamp": time.time(),
                        "data": full_data
                    }
                elif table_name in models_map:
                    records = [r.to_dict() for r in models_map[table_name].query.all()]
                    return {
                        "success": True,
                        "table": table_name,
                        "count": len(records),
                        "timestamp": time.time(),
                        "data": records
                    }
                else:
                    return {"success": False, "error": f"Unknown table_name: {table_name}"}

            elif tool_name == "restore_system_backup":
                table_name = arguments.get("table_name")
                records = arguments.get("records") or []
                if not isinstance(records, list):
                    return {"success": False, "error": "'records' must be a list of objects."}

                count = 0
                if table_name == "teams":
                    for item in records:
                        name_en = str(item.get("name_en", "")).strip().lower()
                        name_he = str(item.get("name_he", "")).strip()
                        if not name_en or not name_he:
                            continue
                        t = Team(id=item.get("id"), name_en=name_en, name_he=name_he)
                        db.session.merge(t) if item.get("id") else db.session.add(t)
                        count += 1
                elif table_name == "projects":
                    for item in records:
                        name = str(item.get("name", "")).strip()
                        if not name:
                            continue
                        p = Project(id=item.get("id"), name=name, is_archived=bool(item.get("is_archived", False)))
                        db.session.merge(p) if item.get("id") else db.session.add(p)
                        count += 1
                elif table_name == "tasks":
                    for item in records:
                        t_title = str(item.get("task", "")).strip()
                        if not t_title:
                            continue
                        m_val = item.get("members", "")
                        members_str = ",".join(m_val) if isinstance(m_val, list) else str(m_val or "")
                        t = Task(
                            id=item.get("id"),
                            project_id=item.get("project_id"),
                            project=str(item.get("project", "כללי")).strip(),
                            task=t_title,
                            members=members_str,
                            status=str(item.get("status", "status-notstarted")),
                            priority=str(item.get("priority", "none")),
                            notes=item.get("notes", ""),
                            team_id=item.get("team_id"),
                            start_date=ai_tools.parse_date_value(item.get("start_date")),
                            end_date=ai_tools.parse_date_value(item.get("end_date")),
                            estimated_hours=float(item["estimated_hours"]) if item.get("estimated_hours") is not None else None,
                            is_archived=bool(item.get("is_archived", False))
                        )
                        db.session.merge(t) if item.get("id") else db.session.add(t)
                        count += 1
                elif table_name == "subtasks":
                    for item in records:
                        title = str(item.get("title", "")).strip()
                        t_id = item.get("task_id")
                        if not title or not t_id:
                            continue
                        s = Subtask(
                            id=item.get("id"),
                            task_id=t_id,
                            title=title,
                            is_completed=bool(item.get("is_completed", False)),
                            order=int(item.get("order", 0))
                        )
                        db.session.merge(s) if item.get("id") else db.session.add(s)
                        count += 1
                elif table_name == "task_comments":
                    for item in records:
                        content = str(item.get("content", "")).strip()
                        t_id = item.get("task_id")
                        if not content or not t_id:
                            continue
                        c = TaskComment(
                            id=item.get("id"),
                            task_id=t_id,
                            author_name=str(item.get("author_name", "חבר צוות")).strip() or "חבר צוות",
                            author_avatar=str(item.get("author_avatar", "default.png")).strip() or "default.png",
                            member_id=item.get("member_id"),
                            content=content
                        )
                        db.session.merge(c) if item.get("id") else db.session.add(c)
                        count += 1
                else:
                    return {"success": False, "error": f"Unsupported restore table: {table_name}"}

                db.session.commit()
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "table": table_name,
                    "restored_count": count
                }

            elif tool_name == "list_database_backups":
                import backup_service
                backups = backup_service.list_backups(app.instance_path)
                return {
                    "success": True,
                    "backups": backups,
                    "count": len(backups),
                    "retention_limit": 14,
                    "auto_backup_time": "23:00"
                }

            elif tool_name == "create_database_backup":
                import backup_service
                b_type = arguments.get("backup_type", "manual")
                new_backup = backup_service.create_backup(backup_type=b_type, keep_count=14, app_instance_path=app.instance_path)
                _notify_db_change(app, _bump_data_version)
                return {
                    "success": True,
                    "message": "Database backup created successfully",
                    "backup": new_backup
                }

            elif tool_name == "restore_database_backup":
                import backup_service
                filename = arguments.get("filename")
                if not filename:
                    return {"success": False, "error": "'filename' parameter is required"}
                res = backup_service.restore_backup(filename, app=app, db=db, on_version_bump=lambda: _notify_db_change(app, _bump_data_version))
                return res

            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error executing MCP tool '{tool_name}': {e}", exc_info=True)
            return {"success": False, "error": str(e)}


# ============================================================================
# RESOURCE & PROMPT HANDLERS
# ============================================================================

def read_mcp_resource(uri: str) -> dict:
    """Reads an MCP resource or dynamic resource template by URI."""
    app, db, Team, TeamMember, Project, Task, SpecialDay, _, _, ai_tools, ai_context, _ = _get_flask_context()
    with app.app_context():
        if uri == "teamtasks://context/snapshot":
            data = ai_context.build_system_context()
        elif uri == "teamtasks://analytics/executive-summary":
            data = ai_context.get_executive_summary()
        elif uri == "teamtasks://analytics/deadlines":
            data = ai_context.get_deadlines_analysis()
        elif uri == "teamtasks://analytics/suggestions":
            data = ai_context.get_stale_and_suggestions()
        elif uri == "teamtasks://catalog/teams":
            data = [t.to_dict() for t in Team.query.all()]
        elif uri == "teamtasks://catalog/projects":
            data = [p.to_dict() for p in Project.query.all()]
        elif uri.startswith("teamtasks://projects/"):
            proj_name = uri.split("teamtasks://projects/", 1)[1]
            data = execute_mcp_tool("get_project", {"name": proj_name})
        elif uri.startswith("teamtasks://teams/"):
            team_name = uri.split("teamtasks://teams/", 1)[1]
            data = execute_mcp_tool("list_tasks", {"team": team_name})
        elif uri.startswith("teamtasks://members/"):
            member_name = uri.split("teamtasks://members/", 1)[1]
            data = execute_mcp_tool("list_tasks", {"member": member_name})
        else:
            raise ValueError(f"Unknown resource URI: {uri}")

        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(data, ensure_ascii=False, indent=2)
                }
            ]
        }


def get_mcp_prompt(prompt_name: str, arguments: dict = None) -> dict:
    """Generates a contextualized MCP prompt with live system data."""
    arguments = arguments or {}
    app, db, _, _, _, _, _, _, _, _, ai_context, _ = _get_flask_context()
    with app.app_context():
        if prompt_name == "daily-standup-report":
            team_filter = arguments.get("team", "")
            summary = ai_context.get_executive_summary()
            deadlines = ai_context.get_deadlines_analysis()
            scope_text = f" עבור צוות {team_filter}" if team_filter else " עבור כלל הצוותים במערכת"
            prompt_text = (
                f"אנא הפק דוח Daily Standup מפורט וברור בעברית{scope_text}.\n\n"
                f"נתוני אמת מהמערכת:\n"
                f"{json.dumps({'summary': summary, 'deadlines': deadlines}, ensure_ascii=False, indent=2)}\n\n"
                f"כלול בדוח:\n"
                f"1. משימות בביצוע כעת (בתהליך)\n"
                f"2. משימות שהושלמו\n"
                f"3. חסמים, משימות מעוכבות או באיחור (Overdue)\n"
                f"4. מיקוד מומלץ להיום"
            )
            return {
                "description": "Daily Standup & Blockers Report",
                "messages": [{"role": "user", "content": {"type": "text", "text": prompt_text}}]
            }

        elif prompt_name == "sprint-planning-assistant":
            team_filter = arguments.get("team", "")
            suggestions = ai_context.get_stale_and_suggestions()
            summary = ai_context.get_executive_summary()
            prompt_text = (
                f"אתה עוזר תכנון ספרינט (Sprint Planning Assistant) של מערכת TeamTasks.\n"
                f"נתח את עומסי העבודה של חברי הצוות, משימות ללא משויך, ומשימות ללא הערכת שעות:\n"
                f"{json.dumps({'workload': summary.get('member_workload'), 'suggestions': suggestions}, ensure_ascii=False, indent=2)}\n\n"
                f"הצע תוכנית עבודה מאוזנת ושיבוץ מומלץ של משימות פתוחות לחברי הצוות הפנויים."
            )
            return {
                "description": "Sprint Planning & Workload Allocation Assistant",
                "messages": [{"role": "user", "content": {"type": "text", "text": prompt_text}}]
            }

        elif prompt_name == "project-health-audit":
            proj_name = arguments.get("project", "")
            data = execute_mcp_tool("get_project", {"name": proj_name}) if proj_name else ai_context.get_executive_summary()
            prompt_text = (
                f"בצע ביקורת בריאות פרויקטים (Project Health Audit) על סמך הנתונים הבאים:\n"
                f"{json.dumps(data, ensure_ascii=False, indent=2)}\n\n"
                f"זהה סיכונים, צווארי בקבוק, משימות ללא תאריך יעד, והמלץ על פעולות מתקנות."
            )
            return {
                "description": "Project Health & Risk Audit",
                "messages": [{"role": "user", "content": {"type": "text", "text": prompt_text}}]
            }

        elif prompt_name == "team-workload-balancer":
            summary = ai_context.get_executive_summary()
            prompt_text = (
                f"נתח את התפלגות עומסי העבודה הנוכחית בין חברי הצוות:\n"
                f"{json.dumps(summary.get('member_workload'), ensure_ascii=False, indent=2)}\n\n"
                f"זהה מי מהעובדים בעומס יתר ומי פנוי, והצע העברת משימות קונקרטית לאיזון העומסים."
            )
            return {
                "description": "Team Workload Balancer",
                "messages": [{"role": "user", "content": {"type": "text", "text": prompt_text}}]
            }

        else:
            raise ValueError(f"Unknown prompt name: {prompt_name}")


# ============================================================================
# JSON-RPC 2.0 MCP PROTOCOL DISPATCHER
# ============================================================================

def handle_mcp_jsonrpc_message(message: dict) -> dict | None:
    """
    Processes a single JSON-RPC 2.0 MCP message and returns a JSON-RPC response dict,
    or None if the message is a notification (no 'id').
    """
    if not isinstance(message, dict):
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": "Invalid Request"}
        }

    method = message.get("method", "")
    msg_id = message.get("id")
    params = message.get("params") or {}

    # Notifications do not have an 'id' and expect no response
    if msg_id is None and method.startswith("notifications/"):
        return None

    try:
        if method == "initialize":
            client_version = params.get("protocolVersion", DEFAULT_PROTOCOL_VERSION)
            negotiated_version = client_version if client_version in SUPPORTED_PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": negotiated_version,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "prompts": {"listChanged": False},
                        "logging": {}
                    },
                    "serverInfo": {
                        "name": MCP_SERVER_NAME,
                        "version": MCP_SERVER_VERSION
                    },
                    "instructions": (
                        "TeamTasks MCP Server provides full management of tasks, projects, teams, "
                        "team members, calendar schedules, workload capacity, special days, analytics, "
                        "and system backups. Supports both Hebrew and English entity names."
                    )
                }
            }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        elif method == "logging/setLevel":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        elif method == "tools/list":
            clean_tools = [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": t["inputSchema"]
                }
                for t in MCP_TOOLS
            ]
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": clean_tools}
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments") or {}
            if not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32602, "message": "Missing tool 'name' in params"}
                }

            known_names = {t["name"] for t in MCP_TOOLS}
            if tool_name not in known_names:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}
                }

            result_obj = execute_mcp_tool(tool_name, arguments)
            is_error = not result_obj.get("success", True)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result_obj, ensure_ascii=False, indent=2)
                        }
                    ],
                    "isError": is_error
                }
            }

        elif method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"resources": MCP_RESOURCES}
            }

        elif method == "resources/templates/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"resourceTemplates": MCP_RESOURCE_TEMPLATES}
            }

        elif method == "resources/read":
            uri = params.get("uri")
            if not uri:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32602, "message": "Missing resource 'uri'"}
                }
            res_data = read_mcp_resource(uri)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": res_data
            }

        elif method == "prompts/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"prompts": MCP_PROMPTS}
            }

        elif method == "prompts/get":
            prompt_name = params.get("name")
            prompt_args = params.get("arguments") or {}
            res_prompt = get_mcp_prompt(prompt_name, prompt_args)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": res_prompt
            }

        else:
            if msg_id is None:
                return None
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

    except Exception as e:
        logger.error(f"Error handling JSON-RPC method {method}: {e}", exc_info=True)
        if msg_id is None:
            return None
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
        }


# ============================================================================
# STDIO SERVER LOOP
# ============================================================================

def run_stdio_server():
    """
    Runs the MCP Server over standard input/output (newline-delimited JSON-RPC 2.0).
    Compatible with Claude Desktop, Cursor, Antigravity, Windsurf, and VS Code MCP clients.
    """
    # Ensure UTF-8 encoding on Windows stdin/stdout
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    real_stdout = sys.stdout
    # Redirect sys.stdout to sys.stderr during execution so stray prints never corrupt JSON-RPC
    sys.stdout = sys.stderr

    logger.info(f"Starting {MCP_SERVER_NAME} v{MCP_SERVER_VERSION} on stdio transport...")

    try:
        for raw_line in sys.stdin:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as je:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(je)}"}
                }
                real_stdout.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
                real_stdout.flush()
                continue

            if isinstance(payload, list):
                responses = []
                for item in payload:
                    r = handle_mcp_jsonrpc_message(item)
                    if r is not None:
                        responses.append(r)
                if responses:
                    real_stdout.write(json.dumps(responses, ensure_ascii=False) + "\n")
                    real_stdout.flush()
            else:
                response = handle_mcp_jsonrpc_message(payload)
                if response is not None:
                    real_stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                    real_stdout.flush()
    except KeyboardInterrupt:
        logger.info("MCP stdio server stopped.")
    finally:
        sys.stdout = real_stdout


def main():
    parser = argparse.ArgumentParser(description="TeamTasks MCP Server for AI Agents")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="Transport protocol: 'stdio' (default) or 'http'"
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "0.0.0.0"),
        help="Host to bind when running in HTTP mode (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "5000")),
        help="Port to bind when running in HTTP mode (default: 5000)"
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        run_stdio_server()
    else:
        app, *_ = _get_flask_context()
        logger.info(f"Starting TeamTasks HTTP + MCP Server on http://{args.host}:{args.port}/mcp")
        app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()

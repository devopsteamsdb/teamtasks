# -*- coding: utf-8 -*-
"""
Verification suite for MCP Server subtasks and notes/comments capabilities.
Tests both direct execute_mcp_tool and JSON-RPC 2.0 dispatching.
"""

import os
import sys
import json
import unittest

# Ensure repo root is on path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from mcp_server import (
    MCP_TOOLS,
    execute_mcp_tool,
    handle_mcp_jsonrpc_message,
    _get_flask_context
)


class TestMCPSubtasksAndNotes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app, db, Team, TeamMember, Project, Task, SpecialDay, _, _, ai_tools, ai_context, _bump = _get_flask_context()
        cls.app = app
        cls.db = db
        cls.Task = Task
        cls.Project = Project
        cls.Team = Team
        cls.TeamMember = TeamMember
        cls.created_task_ids = []

    def tearDown(self):
        # Clean up any created tasks
        with self.app.app_context():
            from models import Task, Subtask, TaskComment
            for tid in self.created_task_ids:
                t = self.db.session.get(Task, tid)
                if t:
                    Subtask.query.filter_by(task_id=tid).delete()
                    TaskComment.query.filter_by(task_id=tid).delete()
                    self.db.session.delete(t)
            self.db.session.commit()
            self.created_task_ids.clear()

    def test_01_tool_schemas_registered(self):
        """Verify new tools and schema enhancements exist in MCP_TOOLS."""
        tool_names = {t["name"] for t in MCP_TOOLS}
        expected_new_tools = {
            "list_subtasks",
            "create_subtask",
            "update_subtask",
            "delete_subtask",
            "list_task_comments",
            "create_task_comment",
            "delete_task_comment"
        }
        for name in expected_new_tools:
            self.assertIn(name, tool_names, f"Expected tool '{name}' in MCP_TOOLS")

        # Check create_task schema has subtasks and notes
        create_task_schema = next(t for t in MCP_TOOLS if t["name"] == "create_task")
        props = create_task_schema["inputSchema"]["properties"]
        self.assertIn("notes", props)
        self.assertIn("subtasks", props)

        # Check update_task schema has notes, append_notes, and add_subtasks
        update_task_schema = next(t for t in MCP_TOOLS if t["name"] == "update_task")
        up_props = update_task_schema["inputSchema"]["properties"]
        self.assertIn("notes", up_props)
        self.assertIn("append_notes", up_props)
        self.assertIn("add_subtasks", up_props)

    def test_02_create_task_with_notes_and_subtasks(self):
        """Test creating a task with initial notes and subtasks via MCP."""
        res = execute_mcp_tool("create_task", {
            "project": "בדיקות אוטומציה",
            "task": "משימת בדיקת MCP תתי-משימות והערות",
            "notes": "הערת בדיקה ראשונית עבור MCP",
            "subtasks": [
                "תת-משימה 1: איפיון דרישות",
                "תת-משימה 2: פיתוח קוד",
                "תת-משימה 3: בדיקת איכות QA"
            ]
        })
        self.assertTrue(res.get("success"), f"create_task failed: {res}")
        task_data = res.get("task")
        self.assertIsNotNone(task_data)
        task_id = task_data["id"]
        self.created_task_ids.append(task_id)

        self.assertEqual(task_data["notes"], "הערת בדיקה ראשונית עבור MCP")
        self.assertEqual(task_data["subtasks_count"], 3)
        self.assertEqual(task_data["subtasks_completed_count"], 0)
        self.assertEqual(len(task_data["subtasks"]), 3)
        self.assertEqual(task_data["subtasks"][0]["title"], "תת-משימה 1: איפיון דרישות")
        self.assertFalse(task_data["subtasks"][0]["is_completed"])

    def test_03_get_task_returns_enriched_subtasks_and_comments(self):
        """Verify get_task returns full subtasks and comments detail."""
        res_create = execute_mcp_tool("create_task", {
            "project": "בדיקות אוטומציה",
            "task": "בדיקת get_task העשרה",
            "notes": "פרטי משימה נרחבים",
            "subtasks": ["צ'קליסט א'"]
        })
        task_id = res_create["task"]["id"]
        self.created_task_ids.append(task_id)

        res_get = execute_mcp_tool("get_task", {"id": task_id})
        self.assertTrue(res_get.get("success"))
        t = res_get["task"]
        self.assertEqual(t["notes"], "פרטי משימה נרחבים")
        self.assertIn("subtasks", t)
        self.assertIn("comments", t)
        self.assertEqual(len(t["subtasks"]), 1)

    def test_04_subtask_crud_tools(self):
        """Verify create_subtask, update_subtask, list_subtasks, delete_subtask tools."""
        res_create = execute_mcp_tool("create_task", {
            "project": "בדיקות אוטומציה",
            "task": "משימה לבדיקת כלי CRUD תתי-משימות"
        })
        task_id = res_create["task"]["id"]
        self.created_task_ids.append(task_id)

        # 1. create_subtask
        st_res1 = execute_mcp_tool("create_subtask", {
            "task_id": task_id,
            "title": "פריט רשימה ראשון"
        })
        self.assertTrue(st_res1.get("success"))
        st1_id = st_res1["subtask"]["id"]

        st_res2 = execute_mcp_tool("create_subtask", {
            "task_id": task_id,
            "title": "פריט רשימה שני",
            "is_completed": True
        })
        self.assertTrue(st_res2.get("success"))
        st2_id = st_res2["subtask"]["id"]

        # 2. list_subtasks
        list_res = execute_mcp_tool("list_subtasks", {"task_id": task_id})
        self.assertTrue(list_res.get("success"))
        self.assertEqual(list_res["count"], 2)
        self.assertEqual(list_res["completed_count"], 1)

        # 3. update_subtask: toggle st1 to completed
        up_res = execute_mcp_tool("update_subtask", {
            "id": st1_id,
            "is_completed": True,
            "title": "פריט רשימה ראשון - עודכן"
        })
        self.assertTrue(up_res.get("success"))
        self.assertEqual(up_res["subtask"]["title"], "פריט רשימה ראשון - עודכן")
        self.assertTrue(up_res["subtask"]["is_completed"])

        # Check list again: both completed now
        list_res2 = execute_mcp_tool("list_subtasks", {"task_id": task_id})
        self.assertEqual(list_res2["completed_count"], 2)

        # 4. delete_subtask
        del_res = execute_mcp_tool("delete_subtask", {"id": st2_id})
        self.assertTrue(del_res.get("success"))

        list_res3 = execute_mcp_tool("list_subtasks", {"task_id": task_id})
        self.assertEqual(list_res3["count"], 1)
        self.assertEqual(list_res3["subtasks"][0]["id"], st1_id)

    def test_05_task_comments_crud_tools(self):
        """Verify create_task_comment, list_task_comments, delete_task_comment tools."""
        res_create = execute_mcp_tool("create_task", {
            "project": "בדיקות אוטומציה",
            "task": "משימה לבדיקת הערות ותגובות MCP"
        })
        task_id = res_create["task"]["id"]
        self.created_task_ids.append(task_id)

        # 1. create_task_comment
        c_res1 = execute_mcp_tool("create_task_comment", {
            "task_id": task_id,
            "content": "הערה חשובה: נדרש לבדוק את השרת לפני העלאה ל-Prod",
            "author_name": "אלעד המפתח"
        })
        self.assertTrue(c_res1.get("success"), f"create_task_comment failed: {c_res1}")
        c1_id = c_res1["comment"]["id"]
        self.assertEqual(c_res1["comment"]["content"], "הערה חשובה: נדרש לבדוק את השרת לפני העלאה ל-Prod")
        self.assertEqual(c_res1["comment"]["author_name"], "אלעד המפתח")

        c_res2 = execute_mcp_tool("create_task_comment", {
            "task_id": task_id,
            "content": "תגובה שנייה: הכל מוכן ומאושר",
            "member": "itamar"
        })
        self.assertTrue(c_res2.get("success"))
        c2_id = c_res2["comment"]["id"]

        # 2. list_task_comments
        list_res = execute_mcp_tool("list_task_comments", {"task_id": task_id})
        self.assertTrue(list_res.get("success"))
        self.assertEqual(list_res["count"], 2)

        # 3. delete_task_comment
        del_res = execute_mcp_tool("delete_task_comment", {"id": c1_id})
        self.assertTrue(del_res.get("success"))

        list_res2 = execute_mcp_tool("list_task_comments", {"task_id": task_id})
        self.assertEqual(list_res2["count"], 1)
        self.assertEqual(list_res2["comments"][0]["id"], c2_id)

    def test_06_update_task_notes_and_add_subtasks(self):
        """Verify update_task with notes, append_notes, and add_subtasks."""
        res_create = execute_mcp_tool("create_task", {
            "project": "בדיקות אוטומציה",
            "task": "בדיקת עדכון הערות ותתי-משימות מרוכז",
            "notes": "שורה ראשונה"
        })
        task_id = res_create["task"]["id"]
        self.created_task_ids.append(task_id)

        # Append notes and add subtasks in update_task
        up_res = execute_mcp_tool("update_task", {
            "id": task_id,
            "append_notes": "שורה שנייה שנוספה",
            "add_subtasks": ["פריט נוסף א'", "פריט נוסף ב'"]
        })
        self.assertTrue(up_res.get("success"))
        t = up_res["task"]
        self.assertIn("שורה ראשונה", t["notes"])
        self.assertIn("שורה שנייה שנוספה", t["notes"])
        self.assertEqual(t["subtasks_count"], 2)

    def test_07_search_tasks_finds_subtasks_and_comments(self):
        """Verify search_tasks can find tasks by their subtask titles or comment contents."""
        unique_token = "TOKEN_XYZ_987654"
        res_create = execute_mcp_tool("create_task", {
            "project": "בדיקות אוטומציה",
            "task": "משימה לאיתור לפי תת-משימה"
        })
        task_id = res_create["task"]["id"]
        self.created_task_ids.append(task_id)

        execute_mcp_tool("create_subtask", {
            "task_id": task_id,
            "title": f"פריט מיוחד {unique_token}"
        })

        search_res = execute_mcp_tool("search_tasks", {"query": unique_token})
        self.assertTrue(search_res.get("success"))
        found_ids = [t["id"] for t in search_res.get("tasks", [])]
        self.assertIn(task_id, found_ids, f"Task #{task_id} with subtask token was not found in search_tasks")

    def test_08_jsonrpc_protocol_dispatch(self):
        """Verify standard JSON-RPC 2.0 messages for tools/list and tools/call."""
        # Test tools/list
        list_msg = {
            "jsonrpc": "2.0",
            "id": 101,
            "method": "tools/list",
            "params": {}
        }
        resp = handle_mcp_jsonrpc_message(list_msg)
        self.assertIsNotNone(resp)
        tools = resp.get("result", {}).get("tools", [])
        tool_names = {t["name"] for t in tools}
        self.assertIn("create_subtask", tool_names)
        self.assertIn("create_task_comment", tool_names)

        # Test tools/call create_task
        call_msg = {
            "jsonrpc": "2.0",
            "id": 102,
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {
                    "project": "בדיקות אוטומציה",
                    "task": "משימת JSON-RPC בדיקה",
                    "notes": "נוצרה דרך JSON-RPC 2.0",
                    "subtasks": ["RPC Subtask 1"]
                }
            }
        }
        resp2 = handle_mcp_jsonrpc_message(call_msg)
        self.assertIsNotNone(resp2)
        content = resp2.get("result", {}).get("content", [])
        self.assertTrue(len(content) > 0)
        res_data = json.loads(content[0]["text"])
        self.assertTrue(res_data.get("success"))
        t_id = res_data["task"]["id"]
        self.created_task_ids.append(t_id)
        self.assertEqual(res_data["task"]["subtasks_count"], 1)


if __name__ == "__main__":
    unittest.main()

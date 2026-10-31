# -*- coding: utf-8 -*-
"""Export updated MCP tool schemas to Antigravity's lazy tool directory."""
import os
import sys
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import mcp_server

dest_dir = r"C:\Users\eladz\.gemini\antigravity\mcp\teamtasks-remote"
if os.path.exists(dest_dir):
    for tool in mcp_server.MCP_TOOLS:
        fname = os.path.join(dest_dir, f"{tool['name']}.json")
        data = {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["inputSchema"]
        }
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Exported {len(mcp_server.MCP_TOOLS)} tool schemas to {dest_dir}")
else:
    print(f"Directory {dest_dir} not found, skipping schema file export.")

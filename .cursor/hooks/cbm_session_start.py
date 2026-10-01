# -*- coding: utf-8 -*-
"""
codebase-memory-mcp: Session start hook (Cross-platform Python).
Checks graph status on session start and emits low-overhead system message.
Outputs strict JSON on stdout for AI harnesses.
"""
import json
import os
import shutil
import subprocess
import sys

def get_cbm_bin():
    cmd = shutil.which("codebase-memory-mcp")
    if cmd:
        return cmd
    custom_path = r"C:\Users\trcnologia\tools\codebase-memory-mcp\codebase-memory-mcp.exe"
    if os.path.isfile(custom_path):
        return custom_path
    return "codebase-memory-mcp"

def main():
    system_msg = ""
    try:
        repo_root = os.environ.get("WORKSPACE_ROOT")
        if not repo_root:
            res = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode == 0 and res.stdout.strip():
                repo_root = res.stdout.strip()
            else:
                repo_root = os.getcwd()

        cbm = get_cbm_bin()
        res = subprocess.run(
            [cbm, "cli", "list_projects"],
            capture_output=True,
            text=True,
            timeout=10,
            stdin=subprocess.DEVNULL,
            check=False
        )
        if res.stdout:
            first_line = res.stdout.strip().splitlines()[0] if res.stdout.strip() else ""
            system_msg = f"Knowledge Graph Active (CBM): {first_line}"
    except Exception:
        pass
    finally:
        payload = {"suppressOutput": True}
        if system_msg:
            payload["systemMessage"] = system_msg
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()

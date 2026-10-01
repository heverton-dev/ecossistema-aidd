# -*- coding: utf-8 -*-
"""
codebase-memory-mcp: Incremental update hook (Cross-platform Python).
Executes codebase-memory-mcp update after edits/commits without blocking or crashing.
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
        cmd = [cbm, "cli", "index_repository", "--repo-path", repo_root]
        # Executa em segundo plano desacoplado para não atrasar a resposta da IDE
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
    except Exception:
        pass
    finally:
        sys.stdout.write(json.dumps({"suppressOutput": True}) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()

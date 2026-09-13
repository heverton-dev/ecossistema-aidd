# -*- coding: utf-8 -*-
"""
code-review-graph: Session start hook (Cross-platform Python).
Checks graph status on session start and emits low-overhead system message.
Outputs strict JSON on stdout for AI harnesses.
"""
import json
import os
import subprocess
import sys

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

        res = subprocess.run(
            ["code-review-graph", "status", "--repo", repo_root],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        if res.stdout:
            first_line = res.stdout.strip().splitlines()[0] if res.stdout.strip() else ""
            system_msg = f"Knowledge Graph Active: {first_line}"
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

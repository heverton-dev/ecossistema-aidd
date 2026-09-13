# -*- coding: utf-8 -*-
"""
code-review-graph: Incremental update hook (Cross-platform Python).
Executes code-review-graph update after edits/commits without blocking or crashing.
Outputs strict JSON on stdout for AI harnesses.
"""
import json
import os
import subprocess
import sys

def main():
    try:
        # Detect repo root
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

        # Run code-review-graph update silently with timeout
        cmd = ["code-review-graph", "update", "--skip-flows", "--repo", repo_root]
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
            check=False
        )
    except Exception:
        pass
    finally:
        # Must output ONLY JSON on stdout for harnesses like Gemini/Antigravity/Claude
        sys.stdout.write(json.dumps({"suppressOutput": True}) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()

"""Git worktree engine for ORCA ADE orchestration.

Real git commands via subprocess for worktree lifecycle:
create -> merge -> purge. All operations target a git repository
passed as parameter (never the real ecossistema-aidd).

Zero LLM cost — pure deterministic git operations.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitResult:
    """Result of a git command execution."""

    ok: bool
    stdout: str
    stderr: str
    returncode: int


def _run_git(args: list[str], cwd: Path, check: bool = False) -> GitResult:
    """Run a git command and return structured result."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )
    return GitResult(
        ok=result.returncode == 0,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
        returncode=result.returncode,
    )


def criar_worktree(front_name: str, repo_path: Path) -> GitResult:
    """Create a new git worktree for a front.

    Runs: git worktree add ../wt-<front_name> -b orca/<front_name>

    Args:
        front_name: Name of the front (used for branch and worktree dir).
        repo_path: Path to the git repository root.

    Returns:
        GitResult with success/failure info.
    """
    worktree_dir = repo_path / f"wt-{front_name}"
    branch_name = f"orca/{front_name}"

    result = _run_git(
        ["worktree", "add", str(worktree_dir), "-b", branch_name],
        cwd=repo_path,
    )
    return result


def mergear_worktree(front_name: str, repo_path: Path) -> GitResult:
    """Merge a front's branch into the current branch with --no-ff.

    Switches to the main branch first, then merges the orca/<front_name>
    branch. Runs: git merge --no-ff orca/<front_name>

    Args:
        front_name: Name of the front (branch to merge).
        repo_path: Path to the git repository root.

    Returns:
        GitResult with success/failure info.
    """
    branch_name = f"orca/{front_name}"

    # Get current branch to restore later
    current = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
    if not current.ok:
        return current

    original_branch = current.stdout

    # Checkout main branch
    checkout = _run_git(["checkout", original_branch], cwd=repo_path)
    if not checkout.ok:
        return checkout

    # Merge the front branch
    result = _run_git(["merge", "--no-ff", branch_name], cwd=repo_path)
    return result


def purgar_worktree(front_name: str, repo_path: Path) -> GitResult:
    """Remove a worktree and delete its branch.

    Runs:
      git worktree remove ../wt-<front_name> --force
      git branch -D orca/<front_name>

    Args:
        front_name: Name of the front to purge.
        repo_path: Path to the git repository root.

    Returns:
        GitResult of the last operation (branch delete).
    """
    worktree_dir = repo_path / f"wt-{front_name}"
    branch_name = f"orca/{front_name}"

    # Remove worktree. No Windows, um antivirus/OneDrive sincronizando a pasta
    # pode segurar um handle no diretorio por uma fracao de segundo bem depois
    # que o `git worktree remove` ja apagou o conteudo - a remocao do diretorio
    # em si falha com "Permission denied"/"Device or resource busy" de forma
    # transitoria. Poucas tentativas com um pequeno intervalo resolvem sem
    # precisar de limpeza manual a cada corrida.
    remove_result = _run_git(
        ["worktree", "remove", str(worktree_dir), "--force"],
        cwd=repo_path,
    )
    tentativas = 1
    while not remove_result.ok and tentativas < 4 and worktree_dir.exists():
        time.sleep(1.5 * tentativas)
        remove_result = _run_git(
            ["worktree", "remove", str(worktree_dir), "--force"],
            cwd=repo_path,
        )
        tentativas += 1
    if not remove_result.ok:
        return remove_result

    # Delete branch
    branch_result = _run_git(["branch", "-D", branch_name], cwd=repo_path)
    return branch_result

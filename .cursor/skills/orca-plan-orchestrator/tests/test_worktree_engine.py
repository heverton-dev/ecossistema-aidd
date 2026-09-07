"""Tests for worktree_engine.py — real git commands in temp repos."""

import subprocess
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from worktree_engine import criar_worktree, mergear_worktree, purgar_worktree, GitResult


def _run_git_raw(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Raw git command for test setup/verification."""
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository with real commits."""
    repo = tmp_path / "test-repo"
    repo.mkdir()

    _run_git_raw(["init"], repo)
    _run_git_raw(["config", "user.email", "test@test.com"], repo)
    _run_git_raw(["config", "user.name", "Test"], repo)

    # Create initial commits on main
    (repo / "file1.txt").write_text("initial content")
    _run_git_raw(["add", "."], repo)
    _run_git_raw(["commit", "-m", "initial commit"], repo)

    (repo / "file2.txt").write_text("second file")
    _run_git_raw(["add", "."], repo)
    _run_git_raw(["commit", "-m", "second commit"], repo)

    return repo


class TestCreateWorktree:
    """Test worktree creation via real git commands."""

    def test_create_worktree_success(self, git_repo: Path) -> None:
        result = criar_worktree("test-front", git_repo)

        assert result.ok, f"Failed: {result.stderr}"
        assert (git_repo / "wt-test-front").is_dir()
        assert (git_repo / "wt-test-front" / "file1.txt").exists()

        # Verify branch was created
        branches = _run_git_raw(["branch", "--list", "orca/test-front"], git_repo)
        assert "orca/test-front" in branches.stdout

        # Cleanup
        purgar_worktree("test-front", git_repo)

    def test_create_worktree_duplicate_fails(self, git_repo: Path) -> None:
        result1 = criar_worktree("dup-front", git_repo)
        assert result1.ok

        result2 = criar_worktree("dup-front", git_repo)
        assert not result2.ok

        # Cleanup
        purgar_worktree("dup-front", git_repo)


class TestMergeWorktree:
    """Test merge via real git commands."""

    def test_merge_success(self, git_repo: Path) -> None:
        # Create worktree and make a commit in it
        create_result = criar_worktree("merge-test", git_repo)
        assert create_result.ok

        wt_path = git_repo / "wt-merge-test"
        (wt_path / "new_file.txt").write_text("new content from worktree")
        _run_git_raw(["add", "."], wt_path)
        _run_git_raw(["commit", "-m", "worktree commit"], wt_path)

        # Merge
        merge_result = mergear_worktree("merge-test", git_repo)
        assert merge_result.ok, f"Merge failed: {merge_result.stderr}"

        # Verify file exists in main branch
        assert (git_repo / "new_file.txt").exists()

        # Cleanup
        purgar_worktree("merge-test", git_repo)

    def test_merge_without_changes(self, git_repo: Path) -> None:
        """Merge an empty branch (no new commits) — still succeeds."""
        create_result = criar_worktree("empty-merge", git_repo)
        assert create_result.ok

        merge_result = mergear_worktree("empty-merge", git_repo)
        # git merge --no-ff of identical branches still succeeds (creates merge commit)
        assert merge_result.ok

        purgar_worktree("empty-merge", git_repo)


class TestPurgeWorktree:
    """Test worktree purge (remove + branch delete)."""

    def test_purge_removes_worktree_and_branch(self, git_repo: Path) -> None:
        create_result = criar_worktree("purge-test", git_repo)
        assert create_result.ok
        assert (git_repo / "wt-purge-test").exists()

        purge_result = purgar_worktree("purge-test", git_repo)
        assert purge_result.ok

        # Worktree directory should be gone
        assert not (git_repo / "wt-purge-test").exists()

        # Branch should be gone
        branches = _run_git_raw(["branch", "--list", "orca/purge-test"], git_repo)
        assert "orca/purge-test" not in branches.stdout


class TestFullLifecycle:
    """Full lifecycle: create -> modify -> merge -> purge."""

    def test_happy_path(self, git_repo: Path) -> None:
        # Create
        r = criar_worktree("lifecycle", git_repo)
        assert r.ok

        # Modify in worktree
        wt = git_repo / "wt-lifecycle"
        (wt / "feature.txt").write_text("new feature")
        _run_git_raw(["add", "."], wt)
        _run_git_raw(["commit", "-m", "add feature"], wt)

        # Merge
        r = mergear_worktree("lifecycle", git_repo)
        assert r.ok
        assert (git_repo / "feature.txt").exists()

        # Purge
        r = purgar_worktree("lifecycle", git_repo)
        assert r.ok
        assert not (git_repo / "wt-lifecycle").exists()


class TestGateFailedQuarantine:
    """Gate failed path: worktree stays intact, no merge attempted."""

    def test_no_merge_when_gate_fails(self, git_repo: Path) -> None:
        create_result = criar_worktree("quarantine", git_repo)
        assert create_result.ok

        # Simulate a gate failure: worktree has commits, but we DON'T merge
        wt = git_repo / "wt-quarantine"
        (wt / "bad_code.txt").write_text("failed gate")
        _run_git_raw(["add", "."], wt)
        _run_git_raw(["commit", "-m", "gate-failed commit"], wt)

        # Worktree should still exist and have the commit
        assert (git_repo / "wt-quarantine").is_dir()
        assert (wt / "bad_code.txt").exists()

        # Branch should still exist
        branches = _run_git_raw(["branch", "--list", "orca/quarantine"], git_repo)
        assert "orca/quarantine" in branches.stdout

        # Main branch should NOT have the bad file
        assert not (git_repo / "bad_code.txt").exists()

        # Cleanup: purge the quarantined worktree
        purge_result = purgar_worktree("quarantine", git_repo)
        assert purge_result.ok

    def test_quarantine_multiple_fronts(self, git_repo: Path) -> None:
        """Multiple quarantined worktrees coexist without interfering."""
        for i in range(3):
            r = criar_worktree(f"q{i}", git_repo)
            assert r.ok

        # All 3 worktrees exist
        for i in range(3):
            assert (git_repo / f"wt-q{i}").is_dir()

        # Purge all
        for i in range(3):
            r = purgar_worktree(f"q{i}", git_repo)
            assert r.ok

        # All gone
        for i in range(3):
            assert not (git_repo / f"wt-q{i}").exists()

## { MODULE

##
## === DEPENDENCIES
##

## personal
from huginn import manage_log, manage_shell

## local
from pencil_auto_tests import (
    repo_paths,
    system_settings,
)

##
## === SUMMARY ON MAIN
##

_PAGES_BRANCH_REF = "refs/heads/gh-pages"


def _run_git(
    *,
    git_args: list[str],
) -> None:
    manage_shell.run_cmd_and_show_output(
        cmd_parts=["git", *git_args],
        working_directory=repo_paths.REPO_DIR,
    )


def _query_git(
    *,
    git_args: list[str],
) -> str:
    return manage_shell.query_cmd_and_capture_output(
        cmd_parts=["git", *git_args],
        working_directory=repo_paths.REPO_DIR,
    )


def publish_summary(
    *,
    test_name: str,
    summary_name: str,
) -> None:
    """Commit runs/<test-name>/ and push it; refuse if the branch already holds commits that are not pushed."""
    runs_dir_text = f"runs/{test_name}"
    _run_git(git_args=["fetch", "--quiet"])
    unpushed_commits = _query_git(git_args=["rev-list", "@{upstream}..HEAD"])
    if unpushed_commits != "":
        manage_log.exit_with_error("the branch has commits that are not pushed; push or drop them before publishing")
    changed_files = _query_git(git_args=["status", "--porcelain", "--", runs_dir_text])
    if changed_files == "":
        manage_log.log_note(f"{runs_dir_text} has no changes to commit")
        return
    _run_git(git_args=["add", "--", runs_dir_text])
    _run_git(git_args=["commit", "--quiet", "-m", f"add-run({test_name}): {summary_name}.", "--", runs_dir_text])
    _run_git(git_args=["pull", "--rebase", "--autostash", "--quiet"])
    _run_git(git_args=["push", "--quiet"])
    manage_log.log_outcome(
        f"pushed {runs_dir_text}/{summary_name}",
        status=manage_log.OutcomeStatus.SUCCESS,
    )


##
## === RESULTS PAGE ON GH-PAGES
## the branch holds one folder per test name and no history: each push is a new parentless commit that keeps the
## other folders and replaces this one. `--force-with-lease` refuses the push if another host pushed in between.
##


def publish_page(
    *,
    settings: system_settings.SystemSettings,
) -> None:
    test_name = settings.test_name
    remote_branch_line = _query_git(git_args=["ls-remote", "origin", _PAGES_BRANCH_REF])
    old_commit = ""
    if remote_branch_line != "":
        old_commit = remote_branch_line.split()[0]
    git_dir = _query_git(git_args=["rev-parse", "--absolute-git-dir"])
    ## a separate index and the results directory as work tree, so the checkout of main is never touched.
    git_with_pages_index = [
        "env",
        f"GIT_INDEX_FILE={git_dir}/pages-index",
        "git",
        "--git-dir",
        git_dir,
        "--work-tree",
        str(settings.results_dir),
    ]
    if old_commit == "":
        pages_base_args = ["read-tree", "--empty"]
    else:
        _run_git(git_args=["fetch", "--quiet", "origin", _PAGES_BRANCH_REF])
        pages_base_args = ["read-tree", old_commit]
    manage_shell.run_cmd_and_show_output(
        cmd_parts=[*git_with_pages_index, *pages_base_args],
        working_directory=settings.results_dir,
    )
    manage_shell.run_cmd_and_show_output(
        cmd_parts=[*git_with_pages_index, "rm", "-r", "--cached", "--quiet", "--ignore-unmatch", "--", test_name],
        working_directory=settings.results_dir,
    )
    manage_shell.run_cmd_and_show_output(
        cmd_parts=[*git_with_pages_index, "add", "--force", "--", test_name],
        working_directory=settings.results_dir,
    )
    tree = manage_shell.run_cmd_and_capture_output(
        cmd_parts=[*git_with_pages_index, "write-tree"],
        working_directory=settings.results_dir,
    )
    new_commit = manage_shell.run_cmd_and_capture_output(
        cmd_parts=["git", "commit-tree", tree, "-m", f"update-folder({test_name}/): replace the results page."],
        working_directory=repo_paths.REPO_DIR,
    )
    _run_git(
        git_args=[
            "push",
            "--quiet",
            f"--force-with-lease={_PAGES_BRANCH_REF}:{old_commit}",
            "origin",
            f"{new_commit}:{_PAGES_BRANCH_REF}",
        ],
    )
    manage_log.log_outcome(
        f"replaced {test_name}/ on gh-pages",
        status=manage_log.OutcomeStatus.SUCCESS,
    )


## } MODULE

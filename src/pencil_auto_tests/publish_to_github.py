## { MODULE

##
## === DEPENDENCIES
##

## stdlib
from pathlib import Path

## personal
from huginn import manage_log, manage_shell

## local
from pencil_auto_tests import system_layouts

##
## === GIT
##


def _run_git(
    *,
    git_args: list[str],
) -> None:
    manage_shell.run_cmd_and_show_output(
        cmd_parts=["git", *git_args],
        working_directory=system_layouts.PENCIL_AUTO_TESTS_DIR,
    )


def _query_git(
    *,
    git_args: list[str],
) -> str:
    return manage_shell.query_cmd_and_capture_output(
        cmd_parts=["git", *git_args],
        working_directory=system_layouts.PENCIL_AUTO_TESTS_DIR,
    )


##
## === TEST SUMMARY ON MAIN
##


def publish_test_summary(
    *,
    system_layout: system_layouts.SystemLayout,
    test_summary_path: Path,
) -> None:
    """Commit the dated and the latest test summary and push them; refuse if the branch holds unpushed commits."""
    summary_file_paths = [
        test_summary_path,
        system_layout.latest_test_summary_path,
    ]
    summary_file_args = [str(_summary_file_path) for _summary_file_path in summary_file_paths]
    commit_message = f"add-file({test_summary_path.name}): test summary of {system_layout.system_name}."
    _run_git(git_args=["fetch", "--quiet"])
    unpushed_commits = _query_git(git_args=["rev-list", "@{upstream}..HEAD"])
    if unpushed_commits != "":
        manage_log.exit_with_error(
            "the branch has commits that are not pushed; push or drop them before publishing",
        )
    changed_files = _query_git(git_args=["status", "--porcelain", "--", *summary_file_args])
    if changed_files == "":
        manage_log.log_note(f"{test_summary_path.name} is already committed")
        return
    _run_git(git_args=["add", "--", *summary_file_args])
    _run_git(git_args=["commit", "--quiet", "-m", commit_message, "--", *summary_file_args])
    _run_git(git_args=["pull", "--rebase", "--autostash", "--quiet"])
    _run_git(git_args=["push", "--quiet"])
    manage_log.log_outcome(
        f"pushed {test_summary_path.name}",
        status=manage_log.OutcomeStatus.SUCCESS,
    )


##
## === TEST REPORT ON GH-PAGES
## the branch holds the latest test report and test logs of each system, one folder per system, and no history: each
## push is a new parentless commit that keeps the other folders and replaces this one. `--force-with-lease` refuses
## the push if another machine pushed in between.
##

_GITHUB_PAGES_BRANCH_REF = "refs/heads/gh-pages"


def publish_test_report(
    *,
    system_layout: system_layouts.SystemLayout,
) -> None:
    system_name = system_layout.system_name
    test_logs_dir = system_layout.test_logs_dir
    ls_remote_output = _query_git(git_args=["ls-remote", "origin", _GITHUB_PAGES_BRANCH_REF])
    remote_pages_commit = ""
    if ls_remote_output != "":
        ls_remote_fields = ls_remote_output.split()
        remote_pages_commit = ls_remote_fields[0]
    git_dir = _query_git(git_args=["rev-parse", "--absolute-git-dir"])
    pages_git_cmd = [
        "env",
        f"GIT_INDEX_FILE={git_dir}/pages-index",
        "git",
        "--git-dir",
        git_dir,
        "--work-tree",
        str(test_logs_dir),
    ]
    if remote_pages_commit == "":
        pages_base_args = ["read-tree", "--empty"]
    else:
        _run_git(git_args=["fetch", "--quiet", "origin", _GITHUB_PAGES_BRANCH_REF])
        pages_base_args = ["read-tree", remote_pages_commit]
    manage_shell.run_cmd_and_show_output(
        cmd_parts=[*pages_git_cmd, *pages_base_args],
        working_directory=test_logs_dir,
    )
    manage_shell.run_cmd_and_show_output(
        cmd_parts=[*pages_git_cmd, "rm", "-r", "--cached", "--quiet", "--ignore-unmatch", "--", system_name],
        working_directory=test_logs_dir,
    )
    manage_shell.run_cmd_and_show_output(
        cmd_parts=[*pages_git_cmd, "add", "--force", "--", system_name],
        working_directory=test_logs_dir,
    )
    pages_tree = manage_shell.run_cmd_and_capture_output(
        cmd_parts=[*pages_git_cmd, "write-tree"],
        working_directory=test_logs_dir,
    )
    pages_commit_message = f"update-folder({system_name}/): replace the latest test logs and test report."
    new_pages_commit = manage_shell.run_cmd_and_capture_output(
        cmd_parts=["git", "commit-tree", pages_tree, "-m", pages_commit_message],
        working_directory=system_layouts.PENCIL_AUTO_TESTS_DIR,
    )
    _run_git(
        git_args=[
            "push",
            "--quiet",
            f"--force-with-lease={_GITHUB_PAGES_BRANCH_REF}:{remote_pages_commit}",
            "origin",
            f"{new_pages_commit}:{_GITHUB_PAGES_BRANCH_REF}",
        ],
    )
    manage_log.log_outcome(
        f"replaced {system_name}/ on gh-pages",
        status=manage_log.OutcomeStatus.SUCCESS,
    )


## } MODULE

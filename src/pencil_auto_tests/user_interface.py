## { MODULE

##
## === DEPENDENCIES
##

## stdlib
from pathlib import Path

## personal
from huginn import (
    cmd_args,
    manage_cli,
    manage_log,
    manage_shell,
)

## local
from pencil_auto_tests import (
    host_layout,
    pencil_test_page,
    run_summary,
)

##
## === HELPERS
##


def _get_modified_time_or_none(
    *,
    file_path: Path,
) -> int | None:
    if not file_path.is_file():
        return None
    return file_path.stat().st_mtime_ns


def _fill_trigger_file(
    *,
    trigger_path: Path,
) -> None:
    trigger_path.write_text("filled by pencil_auto_tests\n")


def _summarise_results_page(
    *,
    results_page: Path,
    runs_dir: Path,
) -> None:
    """Turn a `pencil-test --html` results page into a dated summary in `runs_dir`, and copy it to `latest.txt`."""
    if not results_page.is_file():
        manage_log.exit_with_error(f"no results page at {results_page}")
    try:
        run_result = pencil_test_page.read_page_file(page_path=results_page)
    except ValueError as error:
        manage_log.exit_with_error(f"could not read {results_page}: {error}")
    summary_path = run_summary.get_summary_path(
        run_result=run_result,
        runs_dir=runs_dir,
    )
    manage_shell.run_fn(
        description=f"write {summary_path} and copy it to {run_summary.LATEST_FILE_NAME}",
        fn=lambda: run_summary.write_summary_files(
            run_result=run_result,
            runs_dir=runs_dir,
        ),
    )
    num_not_ok_tests = sum(
        1
        for _test_result in run_result.test_results
        if not _test_result.test_is_ok
    )
    manage_log.log_outcome(
        f"summarised the run as {summary_path.name}",
        status=manage_log.OutcomeStatus.SUCCESS,
        items={
            "tests": len(run_result.test_results),
            "not ok": num_not_ok_tests,
        },
    )


##
## === COMMANDS
##


def run_tests(
    *,
    test_root: Path,
    results_dir: Path,
    runs_dir: Path,
    levels: str,
) -> None:
    """Fill the trigger file, call `run-test.sh`, and summarise the run if it produced a new results page."""
    layout = host_layout.HostLayout(
        test_root=test_root.expanduser().resolve(),
        results_dir=results_dir.expanduser().resolve(),
    )
    missing_dirs = layout.get_missing_dirs()
    if len(missing_dirs) > 0:
        missing_dirs_text = ", ".join(str(_missing_dir) for _missing_dir in missing_dirs)
        manage_log.exit_with_error(f"create these before the first run: {missing_dirs_text}")
    page_time_before_run = _get_modified_time_or_none(file_path=layout.results_page_path)
    manage_shell.run_fn(
        description=f"fill {layout.trigger_path}",
        fn=lambda: _fill_trigger_file(trigger_path=layout.trigger_path),
    )
    ## run-test.sh exits non-zero when tests fail, so the new results page, not the exit code, says whether tests ran.
    cmd_run_test_script = [
        "env",
        f"PENCIL_TEST_HOME_DIR={layout.test_root}",
        f"PENCIL_TEST_TARGET_DIR={layout.results_dir}",
        f"PENCIL_TEST_UPDATE_DIR={layout.update_dir}",
        "bash",
        str(host_layout.RUN_TEST_SCRIPT_PATH),
        levels,
        host_layout.TEST_NAME,
    ]
    script_has_succeeded = manage_shell.run_cmd_and_show_output(
        cmd_parts=cmd_run_test_script,
        raise_error=False,
    )
    page_time_after_run = _get_modified_time_or_none(file_path=layout.results_page_path)
    page_is_new = (page_time_after_run is not None) and (page_time_after_run != page_time_before_run)
    if (not page_is_new) and (not script_has_succeeded):
        manage_log.exit_with_error("run-test.sh failed before any tests ran; see its output above")
    if not page_is_new:
        manage_log.log_outcome(
            "trunk has no new commits, so no tests ran",
            status=manage_log.OutcomeStatus.SUCCESS,
        )
        return
    _summarise_results_page(
        results_page=layout.results_page_path,
        runs_dir=runs_dir,
    )


def write_summary(
    *,
    results_page: Path,
    runs_dir: Path,
) -> None:
    _summarise_results_page(
        results_page=results_page,
        runs_dir=runs_dir,
    )


##
## === COMMAND TABLE
##

COMMAND_LINE_TOOL = manage_cli.CommandLineTool(
    name="pencil_auto_tests",
    description="run and publish the intel-bonn Pencil Code auto-tests",
    cmd_groups=[
        manage_cli.CommandGroup(
            title="Running tests",
            cmds=[
                manage_cli.Command(
                    name="run",
                    description="run the tests if trunk has new commits, then summarise the run into runs/",
                    fn=run_tests,
                    args=[
                        cmd_args.NamedArgument(
                            long_arg_name="test-root",
                            description="directory holding the intel-bonn checkout and UPDATE/",
                            input_value_type=cmd_args.InputValueTypes.DIR,
                            is_required=True,
                        ),
                        cmd_args.NamedArgument(
                            long_arg_name="results-dir",
                            description="directory that pencil-test writes intel-bonn/ results into",
                            input_value_type=cmd_args.InputValueTypes.DIR,
                            is_required=True,
                        ),
                        cmd_args.NamedArgument(
                            long_arg_name="runs-dir",
                            description="directory that holds the dated summaries",
                            input_value_type=cmd_args.InputValueTypes.DIR,
                            is_required=True,
                        ),
                        cmd_args.NamedArgument(
                            long_arg_name="levels",
                            description="test levels to run, e.g. 0,1 or 2-3",
                            input_value_type=cmd_args.InputValueTypes.TEXT,
                            is_required=True,
                        ),
                    ],
                ),
            ],
        ),
        manage_cli.CommandGroup(
            title="Publishing results",
            cmds=[
                manage_cli.Command(
                    name="write-summary",
                    description="turn a results page into runs/<date>_r<revision>.txt and copy it to runs/latest.txt",
                    fn=write_summary,
                    args=[
                        cmd_args.NamedArgument(
                            long_arg_name="results-page",
                            description="the index.html that pencil-test wrote",
                            input_value_type=cmd_args.InputValueTypes.PATH,
                            is_required=True,
                        ),
                        cmd_args.NamedArgument(
                            long_arg_name="runs-dir",
                            description="directory that holds the dated summaries",
                            input_value_type=cmd_args.InputValueTypes.DIR,
                            is_required=True,
                        ),
                    ],
                ),
            ],
        ),
    ],
)

##
## === ENTRY POINT
##


def main() -> None:
    log_file_path = manage_log.get_home_log_file_path(tool_name=COMMAND_LINE_TOOL.name)
    manage_log.set_log_file_path(log_file_path=log_file_path)
    manage_cli.run_cli(command_line_tool=COMMAND_LINE_TOOL)


## } MODULE

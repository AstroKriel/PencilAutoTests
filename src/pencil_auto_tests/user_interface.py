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
    pencil_test_page,
    run_summary,
)

##
## === COMMANDS
##


def write_summary(
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
## === COMMAND TABLE
##

COMMAND_LINE_TOOL = manage_cli.CommandLineTool(
    name="pencil_auto_tests",
    description="run and publish the intel-bonn Pencil Code auto-tests",
    cmd_groups=[
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

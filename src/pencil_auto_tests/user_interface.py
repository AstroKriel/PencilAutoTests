## { MODULE

##
## === DEPENDENCIES
##

## stdlib
from pathlib import Path
from typing import ClassVar

## personal
from huginn import (
    cmd_args,
    manage_cli,
    manage_log,
    manage_shell,
)

## local
from pencil_auto_tests import (
    host_setup,
    pencil_test_page,
    publish,
    repo_paths,
    run_summary,
    system_settings,
)

##
## === INPUT VALUE TYPES
##


class InputValueTypes(cmd_args.InputValueTypes):
    TEST_NAME: ClassVar[cmd_args.InputValueType] = cmd_args.InputValueType(
        placeholder_name="test-name",
        convert_fn=str,
    )


##
## === HELPERS
##


def _read_settings_or_exit(
    *,
    test_name: str,
) -> system_settings.SystemSettings:
    settings_path = repo_paths.get_settings_path(test_name=test_name)
    if not settings_path.is_file():
        manage_log.exit_with_error(f"no settings for `{test_name}`: expected {settings_path}")
    try:
        return system_settings.read_settings_file(settings_path=settings_path)
    except ValueError as error:
        manage_log.exit_with_error(f"could not read {settings_path}: {error}")


def _get_modified_time_or_none(
    *,
    file_path: Path,
) -> int | None:
    if not file_path.is_file():
        return None
    return file_path.stat().st_mtime_ns


def _create_dir_if_missing(
    *,
    dir_path: Path,
) -> None:
    if dir_path.is_dir():
        return
    manage_shell.run_fn(
        description=f"create {dir_path}",
        fn=lambda: dir_path.mkdir(parents=True),
    )


def _fill_trigger_file(
    *,
    trigger_path: Path,
) -> None:
    trigger_path.write_text("filled by pencil_auto_tests\n")


def _summarise_results_page(
    *,
    settings: system_settings.SystemSettings,
) -> str:
    """Turn the results page of the test into a dated summary in runs/<test-name>/, and copy it to `latest.txt`."""
    results_page = settings.layout.results_page_path
    runs_dir = repo_paths.get_test_runs_dir(test_name=settings.test_name)
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
    return summary_path.stem


def _summarise_and_publish(
    *,
    settings: system_settings.SystemSettings,
) -> None:
    summary_name = _summarise_results_page(settings=settings)
    publish.publish_summary(
        test_name=settings.test_name,
        summary_name=summary_name,
    )
    publish.publish_page(settings=settings)


##
## === COMMANDS
##


def set_up_test(
    *,
    test: str,
) -> None:
    """Check the required tools, create the test directories, and check out trunk; safe to repeat."""
    settings = _read_settings_or_exit(test_name=test)
    layout = settings.layout
    missing_tools = host_setup.find_missing_tools()
    if len(missing_tools) > 0:
        manage_log.exit_with_error(f"install these first: {', '.join(missing_tools)}")
    _create_dir_if_missing(dir_path=layout.update_dir)
    _create_dir_if_missing(dir_path=layout.test_results_dir)
    if layout.checkout_dir.exists():
        manage_log.log_note(f"{layout.checkout_dir} exists, so trunk is not checked out again")
    else:
        cmd_check_out_trunk = [
            "svn",
            "checkout",
            "--quiet",
            host_setup.PENCIL_SVN_TRUNK_URL,
            str(layout.checkout_dir),
        ]
        manage_shell.run_cmd_and_show_output(cmd_parts=cmd_check_out_trunk)
    manage_log.log_outcome(
        f"`{settings.test_name}` is set up",
        status=manage_log.OutcomeStatus.SUCCESS,
        items={
            "checkout": layout.checkout_dir,
            "results": layout.test_results_dir,
        },
    )


def run_tests(
    *,
    test: str,
) -> None:
    """Fill the trigger file, call `run-test.sh`, and summarise the run if it produced a new results page."""
    settings = _read_settings_or_exit(test_name=test)
    layout = settings.layout
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
        f"PENCIL_AUTO_TEST_OPT={','.join(settings.auto_test_options)}",
        "bash",
        str(repo_paths.RUN_TEST_SCRIPT_PATH),
        settings.levels,
        settings.test_name,
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
    _summarise_and_publish(settings=settings)


def publish_results(
    *,
    test: str,
) -> None:
    settings = _read_settings_or_exit(test_name=test)
    _summarise_and_publish(settings=settings)


def write_summary(
    *,
    test: str,
) -> None:
    settings = _read_settings_or_exit(test_name=test)
    _summarise_results_page(settings=settings)


##
## === COMMAND TABLE
##

_TEST_ARG = cmd_args.NamedArgument(
    long_arg_name="test",
    description="test name; its settings are in systems/<test-name>.toml",
    input_value_type=InputValueTypes.TEST_NAME,
    is_required=True,
)

COMMAND_LINE_TOOL = manage_cli.CommandLineTool(
    name="pencil_auto_tests",
    description="set up, run, and publish Pencil Code auto-tests",
    cmd_groups=[
        manage_cli.CommandGroup(
            title="Running tests",
            cmds=[
                manage_cli.Command(
                    name="setup",
                    description="check the required tools, create the test directories, and check out trunk",
                    fn=set_up_test,
                    args=[_TEST_ARG],
                ),
                manage_cli.Command(
                    name="run",
                    description="run the tests if trunk has new commits, then summarise and publish the run",
                    fn=run_tests,
                    args=[_TEST_ARG],
                ),
            ],
        ),
        manage_cli.CommandGroup(
            title="Publishing results",
            cmds=[
                manage_cli.Command(
                    name="publish",
                    description="summarise the latest results page, push it to main, and replace the folder on gh-pages",
                    fn=publish_results,
                    args=[_TEST_ARG],
                ),
                manage_cli.Command(
                    name="write-summary",
                    description="summarise the latest results page into runs/<test-name>/ without running tests",
                    fn=write_summary,
                    args=[_TEST_ARG],
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

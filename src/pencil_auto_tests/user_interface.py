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
    publish_to_github,
    required_tools,
    system_configs,
    test_reports,
    test_summaries,
)

##
## === INPUT VALUE TYPES
##


class InputValueTypes(cmd_args.InputValueTypes):
    SYSTEM_NAME: ClassVar[cmd_args.InputValueType] = cmd_args.InputValueType(
        placeholder_name="system-name",
        convert_fn=str,
    )


##
## === HELPERS
##

_PENCIL_SVN_TRUNK_URL = "https://pencil-code.org/svn/trunk/"
_BASE_PENCIL_AUTO_TEST_OPTIONS = [
    "--auto-clean",
    "--bisect",
    "--local-lock",
]


def _load_system_config_or_exit(
    *,
    system_name: str,
) -> system_configs.SystemConfig:
    try:
        return system_configs.load_system_config(system_name=system_name)
    except FileNotFoundError:
        manage_log.exit_with_error(
            f"no system config for `{system_name}` in {system_configs.SYSTEM_CONFIGS_DIR}",
        )
    except ValueError as error:
        manage_log.exit_with_error(f"could not load the system config for `{system_name}`: {error}")


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


def _summarise_test_report(
    *,
    system_config: system_configs.SystemConfig,
) -> Path:
    """Turn the latest test report of the system into a dated test summary, copy it to the latest test summary, and
    return the dated test summary path."""
    system_layout = system_config.system_layout
    latest_test_report_path = system_layout.latest_test_report_path
    latest_test_summary_path = system_layout.latest_test_summary_path
    try:
        test_report = test_reports.load_test_report(test_report_path=latest_test_report_path)
    except FileNotFoundError:
        manage_log.exit_with_error(f"no test report at {latest_test_report_path}")
    except ValueError as error:
        manage_log.exit_with_error(f"could not read {latest_test_report_path}: {error}")
    test_summary_path = test_summaries.get_test_summary_path(
        test_report=test_report,
        test_history_dir=system_layout.test_history_dir,
    )
    manage_shell.run_fn(
        description=f"write {test_summary_path} and copy it to {latest_test_summary_path}",
        fn=lambda: test_summaries.write_test_summary_files(
            test_report=test_report,
            test_summary_path=test_summary_path,
            latest_test_summary_path=latest_test_summary_path,
        ),
    )
    num_not_ok_samples = sum(
        1 for _sample_outcome in test_report.sample_outcomes if not _sample_outcome.sample_is_ok
    )
    manage_log.log_outcome(
        f"summarised the test report as {test_summary_path.name}",
        status=manage_log.OutcomeStatus.SUCCESS,
        items={
            "samples": len(test_report.sample_outcomes),
            "not ok": num_not_ok_samples,
        },
    )
    return test_summary_path


def _summarise_and_publish(
    *,
    system_config: system_configs.SystemConfig,
) -> None:
    test_summary_path = _summarise_test_report(system_config=system_config)
    publish_to_github.publish_test_summary(
        system_layout=system_config.system_layout,
        test_summary_path=test_summary_path,
    )
    publish_to_github.publish_test_report(system_layout=system_config.system_layout)


##
## === COMMANDS
##


def set_up_system(
    *,
    system_name: str,
) -> None:
    """Check the required tools, create the system directories, and check out trunk; safe to repeat."""
    system_config = _load_system_config_or_exit(system_name=system_name)
    system_layout = system_config.system_layout
    missing_tools = required_tools.get_missing_tools()
    if len(missing_tools) > 0:
        missing_tool_reasons = {_missing_tool.name: _missing_tool.reason for _missing_tool in missing_tools}
        manage_log.log_note(
            "these tools are missing",
            items=missing_tool_reasons,
        )
        manage_log.exit_with_error("install the missing tools first")
    _create_dir_if_missing(dir_path=system_layout.latest_test_logs_dir)
    if system_layout.pencil_code_dir.exists():
        manage_log.log_note(f"{system_layout.pencil_code_dir} exists, so trunk is not checked out again")
    else:
        cmd_check_out_trunk = [
            "svn",
            "checkout",
            "--quiet",
            _PENCIL_SVN_TRUNK_URL,
            str(system_layout.pencil_code_dir),
        ]
        manage_shell.run_cmd_and_show_output(cmd_parts=cmd_check_out_trunk)
    manage_log.log_outcome(
        f"`{system_config.system_name}` is set up",
        status=manage_log.OutcomeStatus.SUCCESS,
        items={
            "pencil code": system_layout.pencil_code_dir,
            "test logs": system_layout.latest_test_logs_dir,
        },
    )


def run_pencil_tests(
    *,
    system_name: str,
    no_publish: bool,
) -> None:
    """Call `run-test.sh`, which tests only if `svn up` finds new commits, and summarise and publish a new test report."""
    system_config = _load_system_config_or_exit(system_name=system_name)
    system_layout = system_config.system_layout
    missing_dirs = system_layout.get_missing_dirs()
    if len(missing_dirs) > 0:
        missing_dirs_text = ", ".join(str(_missing_dir) for _missing_dir in missing_dirs)
        manage_log.exit_with_error(f"run `setup` first; missing: {missing_dirs_text}")
    report_time_before_run = _get_modified_time_or_none(file_path=system_layout.latest_test_report_path)
    pencil_build_configs_text = "+".join(system_config.pencil_build_configs)
    pencil_auto_test_options = [
        f"--config-files={pencil_build_configs_text}",
        *_BASE_PENCIL_AUTO_TEST_OPTIONS,
    ]
    pencil_auto_test_options_text = ",".join(pencil_auto_test_options)
    cronjob_script_settings = [
        f"PENCIL_TEST_DIR={system_layout.pencil_code_dir}",
        f"PENCIL_TEST_TARGET_DIR={system_layout.test_logs_dir}",
        "PENCIL_TEST_NO_TRIGGER=yes",
        f"PENCIL_AUTO_TEST_OPT={pencil_auto_test_options_text}",
    ]
    if system_config.environment_script is not None:
        environment_script_setting = f"PENCIL_TEST_ENV_SCRIPT={system_config.environment_script}"
        cronjob_script_settings.append(environment_script_setting)
    system_is_untested = report_time_before_run is None
    if system_is_untested:
        cronjob_script_settings.append("PENCIL_TEST_FORCE=yes")
    cmd_run_cronjob_script = [
        "env",
        *cronjob_script_settings,
        "bash",
        str(system_layout.cronjob_script_path),
        system_config.test_levels,
        system_config.system_name,
    ]
    script_has_succeeded = manage_shell.run_cmd_and_show_output(
        cmd_parts=cmd_run_cronjob_script,
        raise_error=False,
    )
    report_time_after_run = _get_modified_time_or_none(file_path=system_layout.latest_test_report_path)
    report_is_new = (report_time_after_run is not None) and (report_time_after_run != report_time_before_run)
    if (not report_is_new) and (not script_has_succeeded):
        manage_log.exit_with_error("run-test.sh failed before any tests ran; see its output above")
    if not report_is_new:
        manage_log.log_outcome(
            "trunk has no new commits, so no tests ran",
            status=manage_log.OutcomeStatus.SUCCESS,
        )
        return
    if no_publish:
        test_summary_path = _summarise_test_report(system_config=system_config)
        manage_log.log_note(f"publishing skipped; the test summary is {test_summary_path}")
        return
    _summarise_and_publish(system_config=system_config)


def publish_latest_test_report(
    *,
    system_name: str,
) -> None:
    system_config = _load_system_config_or_exit(system_name=system_name)
    _summarise_and_publish(system_config=system_config)


def write_test_summary(
    *,
    system_name: str,
) -> None:
    system_config = _load_system_config_or_exit(system_name=system_name)
    _summarise_test_report(system_config=system_config)


##
## === COMMAND TABLE
##

_SYSTEM_NAME_ARG = cmd_args.NamedArgument(
    long_arg_name="system-name",
    description="system to use; its config is system_configs/<system-name>.toml",
    input_value_type=InputValueTypes.SYSTEM_NAME,
    is_required=True,
)
_NO_PUBLISH_FLAG = cmd_args.FlagArgument(
    long_arg_name="no-publish",
    description="write the test summary but push nothing to GitHub, e.g. to try out a system",
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
                    description="check the required tools, create the system directories, and check out trunk",
                    fn=set_up_system,
                    args=[_SYSTEM_NAME_ARG],
                ),
                manage_cli.Command(
                    name="run",
                    description=
                    "run the tests if trunk has new commits, then summarise and publish the test report",
                    fn=run_pencil_tests,
                    args=[_SYSTEM_NAME_ARG, _NO_PUBLISH_FLAG],
                ),
            ],
        ),
        manage_cli.CommandGroup(
            title="Publishing test reports",
            cmds=[
                manage_cli.Command(
                    name="publish",
                    description=
                    "summarise the latest test report, push the summary to main, and replace the folder on gh-pages",
                    fn=publish_latest_test_report,
                    args=[_SYSTEM_NAME_ARG],
                ),
                manage_cli.Command(
                    name="write-test-summary",
                    description=
                    "summarise the latest test report into test_history/<system-name>/ without publishing",
                    fn=write_test_summary,
                    args=[_SYSTEM_NAME_ARG],
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

## { MODULE

##
## === DEPENDENCIES
##

## stdlib
import tempfile
from pathlib import Path

## personal
from huginn import manage_log, manage_shell

## local
from pencil_auto_tests import system_layouts

##
## === CRON LINES
## every line of a system ends in the shell comment `# pencil_auto_tests:<system-name>`, so scheduling again replaces
## those lines and leaves every other line alone.
##

INSTALLED_TOOL_PATH = system_layouts.PENCIL_AUTO_TESTS_DIR / ".venv" / "bin" / "pencil_auto_tests"


def _get_system_marker(
    *,
    system_layout: system_layouts.SystemLayout,
) -> str:
    return f"# pencil_auto_tests:{system_layout.system_name}"


def get_cron_log_path(
    *,
    system_layout: system_layouts.SystemLayout,
) -> Path:
    return system_layout.test_logs_dir / f"cron-{system_layout.system_name}.log"


def get_cron_lines(
    *,
    system_layout: system_layouts.SystemLayout,
) -> list[str]:
    """Run the tests nightly at 02:30, and every hour kill any test process older than three hours."""
    system_marker = _get_system_marker(system_layout=system_layout)
    cron_log_path = get_cron_log_path(system_layout=system_layout)
    test_reaper_path = system_layout.pencil_code_dir / "utils" / "cronjobs" / "test-reaper.sh"
    run_line = (
        f"30 2 * * * {INSTALLED_TOOL_PATH} run --system-name {system_layout.system_name}"
        f" >> {cron_log_path} 2>&1 {system_marker}"
    )
    reaper_line = f"15 * * * * {test_reaper_path} {system_marker}"
    return [run_line, reaper_line]


def _install_crontab(
    *,
    crontab_text: str,
) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        crontab_path = Path(temp_dir) / "crontab"
        crontab_path.write_text(crontab_text)
        manage_shell.run_cmd_and_show_output(cmd_parts=["crontab", str(crontab_path)])


def ensure_cron_lines(
    *,
    system_layout: system_layouts.SystemLayout,
) -> None:
    system_marker = _get_system_marker(system_layout=system_layout)
    current_crontab_text = manage_shell.query_cmd_and_capture_output(
        cmd_parts=["crontab", "-l"],
        raise_error=False,
    )
    current_lines = current_crontab_text.splitlines()
    other_lines = [_line for _line in current_lines if not _line.endswith(system_marker)]
    system_lines = get_cron_lines(system_layout=system_layout)
    new_lines = [*other_lines, *system_lines]
    if new_lines == current_lines:
        manage_log.log_note(f"`{system_layout.system_name}` is already scheduled")
        return
    new_crontab_text = "\n".join(new_lines) + "\n"
    _install_crontab(crontab_text=new_crontab_text)


## } MODULE

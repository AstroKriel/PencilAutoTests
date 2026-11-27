## { U-TEST

##
## === DEPENDENCIES
##

## stdlib
from pathlib import Path

## third-party
import pytest

## personal
from huginn import manage_log, manage_shell

## local
from pencil_auto_tests import (
    cron_schedules,
    system_layouts,
)

##
## === TEST DATA
##

_SOME_SYSTEM_LAYOUT = system_layouts.SystemLayout(
    system_name="some-system",
    pencil_code_dir=Path("/data/pencil/some-system"),
    test_logs_dir=Path("/data/pencil/test-logs"),
)


class _FakeCrontab:
    """Stands in for `crontab -l` and `crontab <file>`, so no test touches the real crontab."""

    def __init__(
        self,
        *,
        crontab_text: str,
    ) -> None:
        self.crontab_text: str = crontab_text
        self.num_installs: int = 0

    def query(
        self,
        **_kwargs: object,
    ) -> str:
        return self.crontab_text.strip()

    def install(
        self,
        *,
        crontab_text: str,
    ) -> None:
        self.crontab_text = crontab_text
        self.num_installs += 1


@pytest.fixture
def some_crontab(
    monkeypatch: pytest.MonkeyPatch,
) -> _FakeCrontab:
    manage_log.set_log_file_path(log_file_path=None)
    some_crontab = _FakeCrontab(crontab_text="0 * * * * some-other-job\n")
    monkeypatch.setattr(manage_shell, "query_cmd_and_capture_output", some_crontab.query)
    monkeypatch.setattr(cron_schedules, "_install_crontab", some_crontab.install)
    return some_crontab


##
## === TEST SUITE
##


class TestGetCronLines:

    def test_lines_run_the_installed_tool_and_the_reaper(
        self,
    ) -> None:
        run_line, reaper_line = cron_schedules.get_cron_lines(system_layout=_SOME_SYSTEM_LAYOUT)
        assert run_line.startswith(
            f"30 2 * * * {cron_schedules.INSTALLED_TOOL_PATH} run --system-name some-system",
        )
        assert ">> /data/pencil/test-logs/cron-some-system.log 2>&1" in run_line
        assert reaper_line.startswith("15 * * * * /data/pencil/some-system/utils/cronjobs/test-reaper.sh")
        for cron_line in (run_line, reaper_line):
            assert cron_line.endswith("# pencil_auto_tests:some-system")


class TestEnsureCronLines:

    def test_other_lines_are_kept(
        self,
        some_crontab: _FakeCrontab,
    ) -> None:
        cron_schedules.ensure_cron_lines(system_layout=_SOME_SYSTEM_LAYOUT)
        crontab_lines = some_crontab.crontab_text.splitlines()
        assert crontab_lines == [
            "0 * * * * some-other-job",
            *cron_schedules.get_cron_lines(system_layout=_SOME_SYSTEM_LAYOUT),
        ]

    def test_scheduling_again_changes_nothing(
        self,
        some_crontab: _FakeCrontab,
    ) -> None:
        cron_schedules.ensure_cron_lines(system_layout=_SOME_SYSTEM_LAYOUT)
        cron_schedules.ensure_cron_lines(system_layout=_SOME_SYSTEM_LAYOUT)
        assert some_crontab.num_installs == 1

    def test_old_lines_of_the_system_are_replaced(
        self,
        some_crontab: _FakeCrontab,
    ) -> None:
        some_crontab.crontab_text += "0 3 * * * some-old-command # pencil_auto_tests:some-system\n"
        cron_schedules.ensure_cron_lines(system_layout=_SOME_SYSTEM_LAYOUT)
        assert "some-old-command" not in some_crontab.crontab_text


## } U-TEST

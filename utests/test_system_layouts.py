## { U-TEST

##
## === DEPENDENCIES
##

## stdlib
from pathlib import Path

## local
from pencil_auto_tests import system_layouts

##
## === TEST SUITE
##


class TestSystemLayout_MissingDirs:

    def _make_some_system_layout(
        self,
        *,
        tmp_path: Path,
    ) -> system_layouts.SystemLayout:
        return system_layouts.SystemLayout(
            system_name="some-system",
            pencil_code_dir=tmp_path / "pencil-code",
            test_logs_dir=tmp_path / "test-logs",
        )

    def test_complete_layout_reports_nothing_missing(
        self,
        tmp_path: Path,
    ) -> None:
        some_system_layout = self._make_some_system_layout(tmp_path=tmp_path)
        some_system_layout.pencil_code_dir.mkdir(parents=True)
        some_system_layout.latest_test_logs_dir.mkdir(parents=True)
        assert some_system_layout.get_missing_dirs() == []

    def test_only_the_missing_logs_dir_is_reported(
        self,
        tmp_path: Path,
    ) -> None:
        some_system_layout = self._make_some_system_layout(tmp_path=tmp_path)
        some_system_layout.pencil_code_dir.mkdir(parents=True)
        assert some_system_layout.get_missing_dirs() == [tmp_path / "test-logs" / "some-system"]


class TestSystemLayout_RepoPaths:

    def test_repo_paths_sit_in_this_repository(
        self,
        tmp_path: Path,
    ) -> None:
        some_system_layout = system_layouts.SystemLayout(
            system_name="some-system",
            pencil_code_dir=tmp_path / "pencil-code",
            test_logs_dir=tmp_path / "test-logs",
        )
        assert some_system_layout.test_history_dir == (
            system_layouts.PENCIL_AUTO_TESTS_DIR / "test_history" / "some-system"
        )
        assert some_system_layout.cronjob_script_path.is_file()


## } U-TEST

## { U-TEST

##
## === DEPENDENCIES
##

## stdlib
from pathlib import Path

## local
from pencil_auto_tests import host_layout

##
## === TEST SUITE
##


class TestHostLayout_MissingDirs:

    def test_complete_layout_reports_nothing_missing(
        self,
        tmp_path: Path,
    ) -> None:
        layout = host_layout.HostLayout(
            test_root=tmp_path / "test-root",
            results_dir=tmp_path / "results",
        )
        layout.checkout_dir.mkdir(parents=True)
        layout.update_dir.mkdir(parents=True)
        layout.test_results_dir.mkdir(parents=True)
        assert layout.get_missing_dirs() == []

    def test_only_the_missing_results_dir_is_reported(
        self,
        tmp_path: Path,
    ) -> None:
        layout = host_layout.HostLayout(
            test_root=tmp_path / "test-root",
            results_dir=tmp_path / "results",
        )
        layout.checkout_dir.mkdir(parents=True)
        layout.update_dir.mkdir(parents=True)
        assert layout.get_missing_dirs() == [tmp_path / "results" / host_layout.TEST_NAME]


## } U-TEST

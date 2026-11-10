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

    def _make_layout(
        self,
        *,
        tmp_path: Path,
    ) -> host_layout.HostLayout:
        return host_layout.HostLayout(
            test_name="some-test",
            test_root=tmp_path / "test-root",
            results_dir=tmp_path / "results",
        )

    def test_complete_layout_reports_nothing_missing(
        self,
        tmp_path: Path,
    ) -> None:
        layout = self._make_layout(tmp_path=tmp_path)
        layout.checkout_dir.mkdir(parents=True)
        layout.update_dir.mkdir(parents=True)
        layout.test_results_dir.mkdir(parents=True)
        assert layout.get_missing_dirs() == []

    def test_only_the_missing_results_dir_is_reported(
        self,
        tmp_path: Path,
    ) -> None:
        layout = self._make_layout(tmp_path=tmp_path)
        layout.checkout_dir.mkdir(parents=True)
        layout.update_dir.mkdir(parents=True)
        assert layout.get_missing_dirs() == [tmp_path / "results" / "some-test"]


## } U-TEST

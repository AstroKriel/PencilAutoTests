## { U-TEST

##
## === DEPENDENCIES
##

## stdlib
import datetime
from pathlib import Path

## local
from pencil_auto_tests import (
    pencil_test_page,
    run_summary,
)

##
## === TEST DATA
##

_RUN_RESULT = pencil_test_page.RunResult(
    start_date=datetime.date(2026, 11, 10),
    svn_revision=46255,
    test_results=[
        pencil_test_page.TestResult(
            test_name="no-modules",
            failed_phase="validating results",
            test_is_finished=False,
        ),
        pencil_test_page.TestResult(
            test_name="most-modules",
            failed_phase=None,
            test_is_finished=True,
        ),
    ],
)

##
## === TEST SUITE
##


class TestWriteSummaryFiles:

    def test_summary_has_one_aligned_line_per_test(
        self,
    ) -> None:
        summary_text = run_summary.format_summary(run_result=_RUN_RESULT)
        assert summary_text == "no-modules    failed validating results\nmost-modules  ok\n"

    def test_dated_file_and_latest_have_the_same_content(
        self,
        tmp_path: Path,
    ) -> None:
        test_history_dir = tmp_path / "test_history"
        run_summary.write_summary_files(
            run_result=_RUN_RESULT,
            test_history_dir=test_history_dir,
        )
        summary_path = run_summary.get_summary_path(
            run_result=_RUN_RESULT,
            test_history_dir=test_history_dir,
        )
        latest_path = test_history_dir / run_summary.LATEST_FILE_NAME
        assert summary_path.name == "2026-11-10_r46255.txt"
        assert latest_path.read_text() == summary_path.read_text()
        assert not latest_path.is_symlink()


## } U-TEST

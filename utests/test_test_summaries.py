## { U-TEST

##
## === DEPENDENCIES
##

## stdlib
import datetime
from pathlib import Path

## local
from pencil_auto_tests import (
    test_reports,
    test_summaries,
)

##
## === TEST DATA
##

_SOME_TEST_REPORT = test_reports.TestReport(
    start_date=datetime.date(2026, 11, 10),
    svn_revision=46255,
    sample_outcomes=[
        test_reports.SampleOutcome(
            sample_name="no-modules",
            failed_phase="validating results",
            sample_is_finished=False,
        ),
        test_reports.SampleOutcome(
            sample_name="most-modules",
            failed_phase=None,
            sample_is_finished=True,
        ),
    ],
)

##
## === TEST SUITE
##


class TestWriteTestSummaryFiles:

    def test_summary_has_one_aligned_line_per_sample(
        self,
    ) -> None:
        summary_text = test_summaries.format_test_summary(test_report=_SOME_TEST_REPORT)
        assert summary_text == "no-modules    failed validating results\nmost-modules  ok\n"

    def test_dated_file_and_latest_have_the_same_content(
        self,
        tmp_path: Path,
    ) -> None:
        test_history_dir = tmp_path / "test_history"
        test_summary_path = test_summaries.get_test_summary_path(
            test_report=_SOME_TEST_REPORT,
            test_history_dir=test_history_dir,
        )
        latest_test_summary_path = test_history_dir / "latest.txt"
        test_summaries.write_test_summary_files(
            test_report=_SOME_TEST_REPORT,
            test_summary_path=test_summary_path,
            latest_test_summary_path=latest_test_summary_path,
        )
        assert test_summary_path.name == "2026-11-10_r46255.txt"
        assert latest_test_summary_path.read_text() == test_summary_path.read_text()
        assert not latest_test_summary_path.is_symlink()


## } U-TEST

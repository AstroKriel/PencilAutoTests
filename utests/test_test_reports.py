## { U-TEST

##
## === DEPENDENCIES
##

## stdlib
import datetime
from pathlib import Path

## third-party
import pytest

## local
from pencil_auto_tests import test_reports

##
## === TEST DATA
## both test reports are real `pencil-test --html` output from level 0 runs at svn revision 46255; the failed run
## had one value in samples/no-modules/reference.out.double changed by hand.
##

_DATA_DIR = Path(__file__).parent / "data"
_PASSED_TEST_REPORT_PATH = _DATA_DIR / "test_report_passed.html"
_FAILED_TEST_REPORT_PATH = _DATA_DIR / "test_report_failed.html"


def _write_test_report(
    *,
    tmp_path: Path,
    start_time_text: str,
    sample_block: str,
) -> Path:
    """Write a minimal test report with one sample, `some-sample`, and return its path."""
    report_text = (
        f"<p>{start_time_text}</p>\n"
        '<div id="div_details">\n'
        '<a id="some-sample"></a>\n'
        f"<pre>{sample_block}</pre>\n"
        "</div>\n"
        '<div id="div_summary">\n'
        "<pre>\nSVN: 100\n</pre>\n"
        "</div>\n"
    )
    test_report_path = tmp_path / "index.html"
    test_report_path.write_text(report_text)
    return test_report_path


def _get_sample_statuses(
    *,
    test_report: test_reports.TestReport,
) -> list[tuple[str, str]]:
    return [
        (_sample_outcome.sample_name, _sample_outcome.status_text)
        for _sample_outcome in test_report.sample_outcomes
    ]


##
## === TEST SUITE
##


class TestLoadTestReport_RealReports:

    def test_passed_report_reads_every_sample_as_ok(
        self,
    ) -> None:
        test_report = test_reports.load_test_report(test_report_path=_PASSED_TEST_REPORT_PATH)
        sample_statuses = _get_sample_statuses(test_report=test_report)
        assert test_report.start_date == datetime.date(2026, 11, 10)
        assert test_report.svn_revision == 46255
        assert sample_statuses == [("no-modules", "ok"), ("most-modules", "ok")]

    def test_failed_report_names_the_failed_phase(
        self,
    ) -> None:
        test_report = test_reports.load_test_report(test_report_path=_FAILED_TEST_REPORT_PATH)
        sample_statuses = _get_sample_statuses(test_report=test_report)
        assert test_report.svn_revision == 46255
        assert sample_statuses == [("no-modules", "failed validating results"), ("most-modules", "ok")]


class TestLoadTestReport_Edges:

    def test_single_digit_day_is_read(
        self,
        tmp_path: Path,
    ) -> None:
        test_report_path = _write_test_report(
            tmp_path=tmp_path,
            start_time_text="Mon Nov  9 02:00:00 2026",
            sample_block="    Validating results..   ok\n",
        )
        test_report = test_reports.load_test_report(test_report_path=test_report_path)
        assert test_report.start_date == datetime.date(2026, 11, 9)

    def test_sample_without_validation_is_unfinished(
        self,
        tmp_path: Path,
    ) -> None:
        test_report_path = _write_test_report(
            tmp_path=tmp_path,
            start_time_text="Mon Nov  9 02:00:00 2026",
            sample_block="    Compiling..   ok\n    Starting..   ok\n",
        )
        test_report = test_reports.load_test_report(test_report_path=test_report_path)
        sample_outcome = test_report.sample_outcomes[0]
        assert sample_outcome.status_text == "unfinished"
        assert not sample_outcome.sample_is_ok

    def test_first_failed_phase_is_reported(
        self,
        tmp_path: Path,
    ) -> None:
        test_report_path = _write_test_report(
            tmp_path=tmp_path,
            start_time_text="Mon Nov  9 02:00:00 2026",
            sample_block=
            "    Compiling..   ok\n    Running..   not ok: 00:10\n    Validating results..   not ok:\n",
        )
        test_report = test_reports.load_test_report(test_report_path=test_report_path)
        sample_outcome = test_report.sample_outcomes[0]
        assert sample_outcome.status_text == "failed running"

    def test_report_without_samples_is_rejected(
        self,
        tmp_path: Path,
    ) -> None:
        report_text = (
            "<p>Mon Nov  9 02:00:00 2026</p>\n"
            '<div id="div_details"></div>\n'
            '<div id="div_summary">SVN: 100\n</div>\n'
        )
        test_report_path = tmp_path / "index.html"
        test_report_path.write_text(report_text)
        with pytest.raises(ValueError, match="no samples"):
            test_reports.load_test_report(test_report_path=test_report_path)


## } U-TEST

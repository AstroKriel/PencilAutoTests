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
from pencil_auto_tests import pencil_test_page

##
## === TEST DATA
## both pages are real `pencil-test --html` output from level 0 runs at svn revision 46255; the failed run
## had one value in samples/no-modules/reference.out.double changed by hand.
##

_DATA_DIR = Path(__file__).parent / "data"
_PASSED_PAGE_PATH = _DATA_DIR / "results_page_passed.html"
_FAILED_PAGE_PATH = _DATA_DIR / "results_page_failed.html"

##
## === TEST SUITE
##


class TestReadPage_RealPages:

    def test_passed_page_reads_every_test_as_ok(
        self,
    ) -> None:
        run_result = pencil_test_page.read_page_file(page_path=_PASSED_PAGE_PATH)
        assert run_result.start_date == datetime.date(2026, 11, 10)
        assert run_result.svn_revision == 46255
        test_statuses = [
            (_test_result.test_name, _test_result.status_text) for _test_result in run_result.test_results
        ]
        assert test_statuses == [("no-modules", "ok"), ("most-modules", "ok")]

    def test_failed_page_names_the_failed_phase(
        self,
    ) -> None:
        run_result = pencil_test_page.read_page_file(page_path=_FAILED_PAGE_PATH)
        assert run_result.svn_revision == 46255
        test_statuses = [
            (_test_result.test_name, _test_result.status_text) for _test_result in run_result.test_results
        ]
        assert test_statuses == [("no-modules", "failed validating results"), ("most-modules", "ok")]


class TestReadPage_Edges:

    def _make_page(
        self,
        *,
        start_time_text: str,
        test_block: str,
    ) -> str:
        return (
            f"<p>{start_time_text}</p>\n"
            '<div id="div_details">\n'
            '<a id="sample"></a>\n'
            f"<pre>{test_block}</pre>\n"
            "</div>\n"
            '<div id="div_summary">\n'
            "<pre>\nSVN: 100\n</pre>\n"
            "</div>\n"
        )

    def test_single_digit_day_is_read(
        self,
    ) -> None:
        page_text = self._make_page(
            start_time_text="Mon Nov  9 02:00:00 2026",
            test_block="    Validating results..   ok\n",
        )
        run_result = pencil_test_page.read_page(page_text=page_text)
        assert run_result.start_date == datetime.date(2026, 11, 9)

    def test_test_without_validation_is_unfinished(
        self,
    ) -> None:
        page_text = self._make_page(
            start_time_text="Mon Nov  9 02:00:00 2026",
            test_block="    Compiling..   ok\n    Starting..   ok\n",
        )
        run_result = pencil_test_page.read_page(page_text=page_text)
        assert run_result.test_results[0].status_text == "unfinished"
        assert not run_result.test_results[0].test_is_ok

    def test_first_failed_phase_is_reported(
        self,
    ) -> None:
        page_text = self._make_page(
            start_time_text="Mon Nov  9 02:00:00 2026",
            test_block=
            "    Compiling..   ok\n    Running..   not ok: 00:10\n    Validating results..   not ok:\n",
        )
        run_result = pencil_test_page.read_page(page_text=page_text)
        assert run_result.test_results[0].status_text == "failed running"

    def test_page_without_tests_is_rejected(
        self,
    ) -> None:
        page_text = (
            "<p>Mon Nov  9 02:00:00 2026</p>\n"
            '<div id="div_details"></div>\n'
            '<div id="div_summary">SVN: 100\n</div>\n'
        )
        with pytest.raises(ValueError, match="no tests"):
            pencil_test_page.read_page(page_text=page_text)


## } U-TEST

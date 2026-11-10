## { MODULE

##
## === DEPENDENCIES
##

## stdlib
import datetime
import re
from dataclasses import dataclass
from pathlib import Path

##
## === PAGE PATTERNS
## `pencil-test --html` writes the run start time in the first <p>, one <pre> block per test after an
## <a id="<test>"> anchor, and the svn revision in the summary <div>.
##

_START_TIME_PATTERN = re.compile(r"<p>(.+?)</p>")
_TEST_ANCHOR_PATTERN = re.compile(r'<a id="([^"]+)"></a>')
_PHASE_PATTERN = re.compile(
    r"^ {4}(?P<phase>[A-Za-z ]+?)\.\.\s.*?(?P<status>not ok|ok)\b",
    flags=re.MULTILINE,
)
_DETAILS_PATTERN = re.compile(
    r'<div id="div_details">(.*?)</div>',
    flags=re.DOTALL,
)
_SUMMARY_PATTERN = re.compile(
    r'<div id="div_summary">(.*?)</div>',
    flags=re.DOTALL,
)
_SVN_REVISION_PATTERN = re.compile(r"^SVN: (\d+)$", flags=re.MULTILINE)
_START_TIME_FORMAT = "%a %b %d %H:%M:%S %Y"
_LAST_PHASE = "validating results"

##
## === RESULTS
##


@dataclass(frozen=True)
class TestResult:
    test_name: str
    failed_phase: str | None
    test_is_finished: bool

    @property
    def test_is_ok(
        self,
    ) -> bool:
        return (self.failed_phase is None) and self.test_is_finished

    @property
    def status_text(
        self,
    ) -> str:
        if self.failed_phase is not None:
            return f"failed {self.failed_phase}"
        if not self.test_is_finished:
            return "unfinished"
        return "ok"


@dataclass(frozen=True)
class RunResult:
    start_date: datetime.date
    svn_revision: int
    test_results: list[TestResult]


##
## === PARSING
##


def _read_test_result(
    *,
    test_name: str,
    test_block: str,
) -> TestResult:
    """Read one test block; the first phase marked `not ok` is the failed phase."""
    phase_matches = list(_PHASE_PATTERN.finditer(test_block))
    failed_phases = [
        _phase_match.group("phase").lower()
        for _phase_match in phase_matches
        if _phase_match.group("status") == "not ok"
    ]
    passed_phases = [
        _phase_match.group("phase").lower()
        for _phase_match in phase_matches
        if _phase_match.group("status") == "ok"
    ]
    failed_phase = None
    if len(failed_phases) > 0:
        failed_phase = failed_phases[0]
    return TestResult(
        test_name=test_name,
        failed_phase=failed_phase,
        test_is_finished=(_LAST_PHASE in passed_phases),
    )


def read_page(
    *,
    page_text: str,
) -> RunResult:
    """Read the start date, svn revision, and per-test results from a `pencil-test --html` page."""
    start_time_match = _START_TIME_PATTERN.search(page_text)
    if start_time_match is None:
        raise ValueError("results page has no start time in a <p> element")
    start_time = datetime.datetime.strptime(start_time_match.group(1), _START_TIME_FORMAT)
    summary_match = _SUMMARY_PATTERN.search(page_text)
    if summary_match is None:
        raise ValueError("results page has no summary section")
    svn_revision_match = _SVN_REVISION_PATTERN.search(summary_match.group(1))
    if svn_revision_match is None:
        raise ValueError("results page summary has no `SVN: <revision>` line")
    details_match = _DETAILS_PATTERN.search(page_text)
    if details_match is None:
        raise ValueError("results page has no details section")
    ## split keeps the captured test names, so the parts alternate: text before the first anchor, then name, block, name, block.
    details_parts = _TEST_ANCHOR_PATTERN.split(details_match.group(1))
    test_names = details_parts[1::2]
    test_blocks = details_parts[2::2]
    if len(test_names) == 0:
        raise ValueError("results page lists no tests")
    test_results = [
        _read_test_result(
            test_name=_test_name,
            test_block=_test_block,
        ) for _test_name, _test_block in zip(test_names, test_blocks)
    ]
    return RunResult(
        start_date=start_time.date(),
        svn_revision=int(svn_revision_match.group(1)),
        test_results=test_results,
    )


def read_page_file(
    *,
    page_path: Path,
) -> RunResult:
    page_text = page_path.read_text()
    return read_page(page_text=page_text)


## } MODULE

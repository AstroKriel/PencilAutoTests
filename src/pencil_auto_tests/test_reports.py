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
## === TEST REPORT PATTERNS
## the test report that `pencil-test --html` writes has the start time in the first <p>, one <pre> block per sample
## after an <a id="<sample>"> anchor, and the svn revision in the summary <div>.
##

_START_TIME_PATTERN = re.compile(r"<p>(.+?)</p>")
_SAMPLE_ANCHOR_PATTERN = re.compile(r'<a id="([^"]+)"></a>')
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
## === TEST REPORT
##


@dataclass(frozen=True)
class SampleOutcome:
    sample_name: str
    failed_phase: str | None
    sample_is_finished: bool

    @property
    def sample_is_ok(
        self,
    ) -> bool:
        return (self.failed_phase is None) and self.sample_is_finished

    @property
    def status_text(
        self,
    ) -> str:
        if self.failed_phase is not None:
            return f"failed {self.failed_phase}"
        if not self.sample_is_finished:
            return "unfinished"
        return "ok"


@dataclass(frozen=True)
class TestReport:
    start_date: datetime.date
    svn_revision: int
    sample_outcomes: list[SampleOutcome]


##
## === EXTRACTING
##


def _extract_start_date(
    *,
    report_text: str,
) -> datetime.date:
    start_time_match = _START_TIME_PATTERN.search(report_text)
    if start_time_match is None:
        raise ValueError("test report has no start time in a <p> element")
    start_time_text = start_time_match.group(1)
    start_time = datetime.datetime.strptime(start_time_text, _START_TIME_FORMAT)
    return start_time.date()


def _extract_svn_revision(
    *,
    report_text: str,
) -> int:
    summary_match = _SUMMARY_PATTERN.search(report_text)
    if summary_match is None:
        raise ValueError("test report has no summary section")
    summary_text = summary_match.group(1)
    svn_revision_match = _SVN_REVISION_PATTERN.search(summary_text)
    if svn_revision_match is None:
        raise ValueError("test report summary has no `SVN: <revision>` line")
    svn_revision_text = svn_revision_match.group(1)
    return int(svn_revision_text)


def _extract_sample_outcome(
    *,
    sample_name: str,
    sample_block: str,
) -> SampleOutcome:
    """The first phase marked `not ok` is the failed phase."""
    phase_matches = list(_PHASE_PATTERN.finditer(sample_block))
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
    sample_is_finished = _LAST_PHASE in passed_phases
    return SampleOutcome(
        sample_name=sample_name,
        failed_phase=failed_phase,
        sample_is_finished=sample_is_finished,
    )


def _extract_sample_outcomes(
    *,
    report_text: str,
) -> list[SampleOutcome]:
    details_match = _DETAILS_PATTERN.search(report_text)
    if details_match is None:
        raise ValueError("test report has no details section")
    details_text = details_match.group(1)
    details_parts = _SAMPLE_ANCHOR_PATTERN.split(details_text)
    sample_names = details_parts[1::2]
    sample_blocks = details_parts[2::2]
    if len(sample_names) == 0:
        raise ValueError("test report lists no samples")
    return [
        _extract_sample_outcome(
            sample_name=_sample_name,
            sample_block=_sample_block,
        ) for _sample_name, _sample_block in zip(sample_names, sample_blocks)
    ]


##
## === LOADING
##


def load_test_report(
    *,
    test_report_path: Path,
) -> TestReport:
    """Load the start date, svn revision, and sample outcomes from a test report written by `pencil-test --html`."""
    report_text = test_report_path.read_text()
    start_date = _extract_start_date(report_text=report_text)
    svn_revision = _extract_svn_revision(report_text=report_text)
    sample_outcomes = _extract_sample_outcomes(report_text=report_text)
    return TestReport(
        start_date=start_date,
        svn_revision=svn_revision,
        sample_outcomes=sample_outcomes,
    )


## } MODULE

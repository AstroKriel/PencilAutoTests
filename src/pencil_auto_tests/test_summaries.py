## { MODULE

##
## === DEPENDENCIES
##

## stdlib
import shutil
from pathlib import Path

## local
from pencil_auto_tests import test_reports

##
## === TEST SUMMARY FILES
##


def format_test_summary(
    *,
    test_report: test_reports.TestReport,
) -> str:
    """One line per sample, in the order the samples ran, with sample names padded so the statuses line up."""
    longest_name_length = max(
        len(_sample_outcome.sample_name) for _sample_outcome in test_report.sample_outcomes
    )
    summary_lines = [
        f"{_sample_outcome.sample_name.ljust(longest_name_length)}  {_sample_outcome.status_text}"
        for _sample_outcome in test_report.sample_outcomes
    ]
    return "\n".join(summary_lines) + "\n"


def get_test_summary_path(
    *,
    test_report: test_reports.TestReport,
    test_history_dir: Path,
) -> Path:
    start_date_text = test_report.start_date.isoformat()
    return test_history_dir / f"{start_date_text}_r{test_report.svn_revision}.txt"


def write_test_summary_files(
    *,
    test_report: test_reports.TestReport,
    test_summary_path: Path,
    latest_test_summary_path: Path,
) -> None:
    """Write the dated test summary, then copy it to the latest test summary."""
    test_summary_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    summary_text = format_test_summary(test_report=test_report)
    test_summary_path.write_text(summary_text)
    shutil.copyfile(test_summary_path, latest_test_summary_path)


## } MODULE

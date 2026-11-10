## { MODULE

##
## === DEPENDENCIES
##

## stdlib
import shutil
from pathlib import Path

## local
from pencil_auto_tests import pencil_test_page

##
## === SUMMARY FILES
##

LATEST_FILE_NAME = "latest.txt"


def format_summary(
    *,
    run_result: pencil_test_page.RunResult,
) -> str:
    """One line per test, in run order, with test names padded so the statuses line up."""
    longest_name_length = max(len(_test_result.test_name) for _test_result in run_result.test_results)
    summary_lines = [
        f"{_test_result.test_name.ljust(longest_name_length)}  {_test_result.status_text}"
        for _test_result in run_result.test_results
    ]
    return "\n".join(summary_lines) + "\n"


def get_summary_path(
    *,
    run_result: pencil_test_page.RunResult,
    test_history_dir: Path,
) -> Path:
    return test_history_dir / f"{run_result.start_date.isoformat()}_r{run_result.svn_revision}.txt"


def write_summary_files(
    *,
    run_result: pencil_test_page.RunResult,
    test_history_dir: Path,
) -> None:
    """Write the dated summary into `test_history_dir`, then copy it to `latest.txt`."""
    test_history_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    summary_text = format_summary(run_result=run_result)
    summary_path = get_summary_path(
        run_result=run_result,
        test_history_dir=test_history_dir,
    )
    summary_path.write_text(summary_text)
    latest_path = test_history_dir / LATEST_FILE_NAME
    shutil.copyfile(summary_path, latest_path)


## } MODULE

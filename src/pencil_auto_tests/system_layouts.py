## { MODULE

##
## === DEPENDENCIES
##

## stdlib
from dataclasses import dataclass
from pathlib import Path

##
## === REPOSITORY
## `uv sync` installs this package in editable mode, so the package sits inside the repo at src/pencil_auto_tests/.
##

_PACKAGE_DIR = Path(__file__).resolve().parent
PENCIL_AUTO_TESTS_DIR = _PACKAGE_DIR.parent.parent

##
## === SYSTEM LAYOUT
## `run-test.sh` takes the Pencil checkout as `TEST_DIR`, the test logs directory as `TARGET_DIR`, and the system
## name as its `TEST`; it writes the latest test logs to <test-logs-dir>/<system-name>/. The dated test summaries of
## the system sit in this repository, in test_history/<system-name>/.
##


@dataclass(frozen=True)
class SystemLayout:
    system_name: str
    pencil_code_dir: Path
    test_logs_dir: Path

    @property
    def latest_test_logs_dir(
        self,
    ) -> Path:
        return self.test_logs_dir / self.system_name

    @property
    def latest_test_report_path(
        self,
    ) -> Path:
        return self.latest_test_logs_dir / "index.html"

    @property
    def test_history_dir(
        self,
    ) -> Path:
        return PENCIL_AUTO_TESTS_DIR / "test_history" / self.system_name

    @property
    def cronjob_script_path(
        self,
    ) -> Path:
        return PENCIL_AUTO_TESTS_DIR / "scripts" / "run-test.sh"

    def get_missing_dirs(
        self,
    ) -> list[Path]:
        """The directories `run-test.sh` needs but does not create; a missing logs directory fails silently."""
        required_dirs = [
            self.pencil_code_dir,
            self.latest_test_logs_dir,
        ]
        return [_required_dir for _required_dir in required_dirs if not _required_dir.is_dir()]


## } MODULE

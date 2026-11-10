## { MODULE

##
## === DEPENDENCIES
##

## stdlib
from dataclasses import dataclass
from pathlib import Path

##
## === LAYOUT
## the test name ties the checkout, the trigger file, and the results directory together; `run-test.sh` names
## <test-root> `HOME_DIR` and <results-dir> `TARGET_DIR`.
##


@dataclass(frozen=True)
class HostLayout:
    test_name: str
    test_root: Path
    results_dir: Path

    @property
    def checkout_dir(
        self,
    ) -> Path:
        return self.test_root / self.test_name

    @property
    def update_dir(
        self,
    ) -> Path:
        return self.test_root / "UPDATE"

    @property
    def trigger_path(
        self,
    ) -> Path:
        return self.update_dir / self.test_name

    @property
    def test_results_dir(
        self,
    ) -> Path:
        return self.results_dir / self.test_name

    @property
    def results_page_path(
        self,
    ) -> Path:
        return self.test_results_dir / "index.html"

    def get_missing_dirs(
        self,
    ) -> list[Path]:
        """The directories `run-test.sh` needs but does not create; a missing results directory fails silently."""
        required_dirs = [
            self.checkout_dir,
            self.update_dir,
            self.test_results_dir,
        ]
        return [
            _required_dir
            for _required_dir in required_dirs
            if not _required_dir.is_dir()
        ]


## } MODULE

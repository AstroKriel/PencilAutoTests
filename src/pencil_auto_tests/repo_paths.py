## { MODULE

##
## === DEPENDENCIES
##

## stdlib
from pathlib import Path

##
## === REPO PATHS
## `uv sync` installs this package in editable mode, so the package sits inside the repo at src/pencil_auto_tests/.
##

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_DIR = PACKAGE_DIR.parent.parent
SYSTEMS_DIR = REPO_DIR / "systems"
RUNS_DIR = REPO_DIR / "runs"
RUN_TEST_SCRIPT_PATH = PACKAGE_DIR / "upstream" / "run-test.sh"


def get_settings_path(
    *,
    test_name: str,
) -> Path:
    return SYSTEMS_DIR / f"{test_name}.toml"


def get_test_runs_dir(
    *,
    test_name: str,
) -> Path:
    return RUNS_DIR / test_name


## } MODULE

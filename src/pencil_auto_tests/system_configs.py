## { MODULE

##
## === DEPENDENCIES
##

## stdlib
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

## local
from pencil_auto_tests import system_layouts

##
## === SYSTEM CONFIG
## one file per system, system_configs/<system-name>.toml, holds everything about how that system runs on its machine.
##

SYSTEM_CONFIGS_DIR = system_layouts.PENCIL_AUTO_TESTS_DIR / "system_configs"
_REQUIRED_KEYS = {
    "pencil_code_dir",
    "test_logs_dir",
    "test_levels",
    "pencil_build_configs",
}
_OPTIONAL_KEYS = {
    "environment_script",
}


@dataclass(frozen=True)
class SystemConfig:
    system_name: str
    pencil_code_dir: Path
    test_logs_dir: Path
    test_levels: str
    pencil_build_configs: list[str]
    environment_script: Path | None

    @property
    def system_layout(
        self,
    ) -> system_layouts.SystemLayout:
        return system_layouts.SystemLayout(
            system_name=self.system_name,
            pencil_code_dir=self.pencil_code_dir,
            test_logs_dir=self.test_logs_dir,
        )


##
## === LOADING
##


def _ensure_expected_keys(
    *,
    config_values: dict[str, Any],
    config_path: Path,
) -> None:
    known_keys = _REQUIRED_KEYS | _OPTIONAL_KEYS
    missing_keys = _REQUIRED_KEYS - config_values.keys()
    unknown_keys = config_values.keys() - known_keys
    if len(missing_keys) > 0:
        raise ValueError(f"`{config_path.name}` is missing keys: {', '.join(sorted(missing_keys))}")
    if len(unknown_keys) > 0:
        raise ValueError(f"`{config_path.name}` has unknown keys: {', '.join(sorted(unknown_keys))}")


def load_system_config(
    *,
    system_name: str,
) -> SystemConfig:
    config_path = SYSTEM_CONFIGS_DIR / f"{system_name}.toml"
    config_text = config_path.read_text()
    config_values = tomllib.loads(config_text)
    _ensure_expected_keys(
        config_values=config_values,
        config_path=config_path,
    )
    pencil_code_dir_text = config_values["pencil_code_dir"]
    pencil_code_dir = Path(pencil_code_dir_text).expanduser()
    test_logs_dir_text = config_values["test_logs_dir"]
    test_logs_dir = Path(test_logs_dir_text).expanduser()
    test_levels = config_values["test_levels"]
    pencil_build_configs = config_values["pencil_build_configs"]
    environment_script = None
    if "environment_script" in config_values:
        environment_script_text = config_values["environment_script"]
        environment_script = Path(environment_script_text).expanduser()
    return SystemConfig(
        system_name=system_name,
        pencil_code_dir=pencil_code_dir,
        test_logs_dir=test_logs_dir,
        test_levels=test_levels,
        pencil_build_configs=pencil_build_configs,
        environment_script=environment_script,
    )


## } MODULE

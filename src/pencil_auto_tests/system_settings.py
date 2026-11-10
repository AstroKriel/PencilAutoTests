## { MODULE

##
## === DEPENDENCIES
##

## stdlib
import re
import tomllib
import typing
from dataclasses import dataclass
from pathlib import Path

## local
from pencil_auto_tests import host_layout

##
## === SETTINGS
## one file per test name, systems/<test-name>.toml, holds everything about how that test runs on its machine.
##

_LEVELS_PATTERN = re.compile(r"[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*")
_EXPECTED_KEYS = {
    "test_root",
    "results_dir",
    "levels",
    "auto_test_options",
}


@dataclass(frozen=True)
class SystemSettings:
    test_name: str
    test_root: Path
    results_dir: Path
    levels: str
    auto_test_options: list[str]

    @property
    def layout(
        self,
    ) -> host_layout.HostLayout:
        return host_layout.HostLayout(
            test_name=self.test_name,
            test_root=self.test_root,
            results_dir=self.results_dir,
        )


##
## === READING
##


def _read_dir(
    *,
    settings: dict[str, object],
    key: str,
) -> Path:
    value = settings[key]
    if not isinstance(value, str):
        raise ValueError(f"`{key}` must be a path in quotes; got {value!r}")
    dir_path = Path(value).expanduser()
    if not dir_path.is_absolute():
        raise ValueError(f"`{key}` must be an absolute path or start with ~; got {value!r}")
    return dir_path


def _read_levels(
    *,
    settings: dict[str, object],
) -> str:
    levels = settings["levels"]
    if (not isinstance(levels, str)) or (_LEVELS_PATTERN.fullmatch(levels) is None):
        raise ValueError(f"`levels` must be text such as \"0\", \"0,1\", or \"2-3\"; got {levels!r}")
    return levels


def _read_auto_test_options(
    *,
    settings: dict[str, object],
) -> list[str]:
    """`run-test.sh` joins these with commas after `--level`, so no option may hold a comma or a space, or set the level."""
    options = settings["auto_test_options"]
    if not isinstance(options, list):
        raise ValueError(f"`auto_test_options` must be a list of text; got {options!r}")
    checked_options: list[str] = []
    for option in typing.cast(list[object], options):
        if not isinstance(option, str):
            raise ValueError(f"`auto_test_options` must be a list of text; got {option!r} in it")
        if (" " in option) or ("," in option):
            raise ValueError(f"`auto_test_options` entries cannot hold commas or spaces; got {option!r}")
        if option.startswith("--level"):
            raise ValueError("`auto_test_options` cannot set the level; use `levels`")
        checked_options.append(option)
    return checked_options


def read_settings_text(
    *,
    test_name: str,
    settings_text: str,
) -> SystemSettings:
    settings = tomllib.loads(settings_text)
    missing_keys = _EXPECTED_KEYS - settings.keys()
    unknown_keys = settings.keys() - _EXPECTED_KEYS
    if len(missing_keys) > 0:
        raise ValueError(f"missing settings: {', '.join(sorted(missing_keys))}")
    if len(unknown_keys) > 0:
        raise ValueError(f"unknown settings: {', '.join(sorted(unknown_keys))}")
    return SystemSettings(
        test_name=test_name,
        test_root=_read_dir(settings=settings, key="test_root"),
        results_dir=_read_dir(settings=settings, key="results_dir"),
        levels=_read_levels(settings=settings),
        auto_test_options=_read_auto_test_options(settings=settings),
    )


def read_settings_file(
    *,
    settings_path: Path,
) -> SystemSettings:
    """The test name is the file name without `.toml`."""
    return read_settings_text(
        test_name=settings_path.stem,
        settings_text=settings_path.read_text(),
    )


## } MODULE

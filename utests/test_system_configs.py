## { U-TEST

##
## === DEPENDENCIES
##

## stdlib
from pathlib import Path

## third-party
import pytest

## local
from pencil_auto_tests import system_configs

##
## === TEST DATA
##

_VALID_CONFIG_TEXT = """
pencil_code_dir = "/data/pencil-code"
test_logs_dir = "/data/test-logs"
test_levels = "0,1"
pencil_build_configs = ["GNU-GCC_MPI", "GNU-GCC_debug"]
"""


def _replace_line(
    *,
    key: str,
    new_line: str,
) -> str:
    replaced_lines: list[str] = []
    for config_line in _VALID_CONFIG_TEXT.splitlines():
        if config_line.startswith(f"{key} ="):
            replaced_lines.append(new_line)
        else:
            replaced_lines.append(config_line)
    return "\n".join(replaced_lines)


def _write_some_system_config(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    config_text: str,
) -> None:
    """Make `tmp_path` the system configs folder, holding the system config of `some-system`."""
    monkeypatch.setattr(system_configs, "SYSTEM_CONFIGS_DIR", tmp_path)
    config_path = tmp_path / "some-system.toml"
    config_path.write_text(config_text)


##
## === TEST SUITE
##


class TestLoadSystemConfig_Valid:

    def test_valid_config_is_loaded(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        _write_some_system_config(
            monkeypatch=monkeypatch,
            tmp_path=tmp_path,
            config_text=_VALID_CONFIG_TEXT,
        )
        system_config = system_configs.load_system_config(system_name="some-system")
        assert system_config.system_name == "some-system"
        assert system_config.system_layout.pencil_code_dir == Path("/data/pencil-code")
        assert system_config.system_layout.latest_test_logs_dir == Path("/data/test-logs/some-system")
        assert system_config.test_levels == "0,1"
        assert system_config.pencil_build_configs == ["GNU-GCC_MPI", "GNU-GCC_debug"]

    def test_home_is_expanded(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        config_text = _replace_line(
            key="pencil_code_dir",
            new_line='pencil_code_dir = "~/pencil-code"',
        )
        _write_some_system_config(
            monkeypatch=monkeypatch,
            tmp_path=tmp_path,
            config_text=config_text,
        )
        system_config = system_configs.load_system_config(system_name="some-system")
        assert system_config.pencil_code_dir == Path.home() / "pencil-code"

    def test_every_system_config_in_the_repo_loads(
        self,
    ) -> None:
        config_paths = sorted(system_configs.SYSTEM_CONFIGS_DIR.glob("*.toml"))
        assert len(config_paths) > 0
        for config_path in config_paths:
            system_configs.load_system_config(system_name=config_path.stem)


class TestLoadSystemConfig_Invalid:

    def test_missing_key_is_rejected(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        config_text = _replace_line(
            key="test_levels",
            new_line='levels = "0"',
        )
        _write_some_system_config(
            monkeypatch=monkeypatch,
            tmp_path=tmp_path,
            config_text=config_text,
        )
        with pytest.raises(ValueError, match="missing keys: test_levels"):
            system_configs.load_system_config(system_name="some-system")

    def test_unknown_system_is_not_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(system_configs, "SYSTEM_CONFIGS_DIR", tmp_path)
        with pytest.raises(FileNotFoundError):
            system_configs.load_system_config(system_name="no-such-system")


## } U-TEST

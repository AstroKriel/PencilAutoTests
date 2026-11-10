## { U-TEST

##
## === DEPENDENCIES
##

## stdlib
from pathlib import Path

## third-party
import pytest

## local
from pencil_auto_tests import (
    repo_paths,
    system_settings,
)

##
## === TEST DATA
##

_VALID_SETTINGS_TEXT = """
test_root = "/data/auto-tests"
results_dir = "/data/auto-tests/results"
levels = "0,1"
auto_test_options = ["--config-files=GNU-GCC_MPI", "--auto-clean"]
"""


def _replace_line(
    *,
    key: str,
    new_line: str,
) -> str:
    settings_lines = _VALID_SETTINGS_TEXT.splitlines()
    replaced_lines = [
        new_line if _line.startswith(f"{key} =") else _line
        for _line in settings_lines
    ]
    return "\n".join(replaced_lines)


##
## === TEST SUITE
##


class TestReadSettings_Valid:

    def test_valid_settings_are_read(
        self,
    ) -> None:
        settings = system_settings.read_settings_text(
            test_name="some-test",
            settings_text=_VALID_SETTINGS_TEXT,
        )
        assert settings.layout.checkout_dir == Path("/data/auto-tests/some-test")
        assert settings.layout.test_results_dir == Path("/data/auto-tests/results/some-test")
        assert settings.levels == "0,1"
        assert settings.auto_test_options == ["--config-files=GNU-GCC_MPI", "--auto-clean"]

    def test_home_is_expanded(
        self,
    ) -> None:
        settings_text = _replace_line(
            key="test_root",
            new_line='test_root = "~/auto-tests"',
        )
        settings = system_settings.read_settings_text(
            test_name="some-test",
            settings_text=settings_text,
        )
        assert settings.test_root == Path.home() / "auto-tests"

    def test_every_settings_file_in_the_repo_is_valid(
        self,
    ) -> None:
        settings_paths = sorted(repo_paths.SYSTEMS_DIR.glob("*.toml"))
        assert len(settings_paths) > 0
        for settings_path in settings_paths:
            system_settings.read_settings_file(settings_path=settings_path)


class TestReadSettings_Invalid:

    @pytest.mark.parametrize(
        ("key", "new_line", "error_text"),
        [
            ("levels", 'levels = "zero"', "`levels`"),
            ("levels", "levels = 0", "`levels`"),
            ("test_root", 'test_root = "relative/path"', "absolute"),
            ("auto_test_options", 'auto_test_options = ["--level=2"]', "cannot set the level"),
            ("auto_test_options", 'auto_test_options = ["--a,--b"]', "commas or spaces"),
            ("auto_test_options", 'auto_test_options = "--auto-clean"', "list of text"),
        ],
    )
    def test_bad_value_is_rejected(
        self,
        key: str,
        new_line: str,
        error_text: str,
    ) -> None:
        settings_text = _replace_line(
            key=key,
            new_line=new_line,
        )
        with pytest.raises(ValueError, match=error_text):
            system_settings.read_settings_text(
                test_name="some-test",
                settings_text=settings_text,
            )

    def test_missing_and_unknown_keys_are_rejected(
        self,
    ) -> None:
        settings_text = _replace_line(
            key="levels",
            new_line='level = "0"',
        )
        with pytest.raises(ValueError, match="missing settings: levels"):
            system_settings.read_settings_text(
                test_name="some-test",
                settings_text=settings_text,
            )


## } U-TEST

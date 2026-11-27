## { U-TEST

##
## === DEPENDENCIES
##

## stdlib
from pathlib import Path

## third-party
import pytest

## personal
from huginn import manage_log

## local
from pencil_auto_tests import versions

##
## === TEST DATA
##


@pytest.fixture(autouse=True)
def _no_log_file() -> None:
    manage_log.set_log_file_path(log_file_path=None)


##
## === TEST SUITE
##


class TestFormatVersionsText:

    def test_header_names_the_tool_commit_and_the_pencil_revision(
        self,
    ) -> None:
        versions_text = versions.format_versions_text(
            svn_revision=46482,
            version_cmds=[],
            environment_script=None,
        )
        header_lines = versions_text.splitlines()
        assert header_lines[0].startswith("pencil_auto_tests  ")
        assert header_lines[0] != "pencil_auto_tests  unknown"
        assert header_lines[1] == "pencil code        r46482"

    def test_each_cmd_is_shown_with_its_output(
        self,
    ) -> None:
        versions_text = versions.format_versions_text(
            svn_revision=1,
            version_cmds=["echo some-compiler 1.0"],
            environment_script=None,
        )
        assert "$ echo some-compiler 1.0\nsome-compiler 1.0\n" in versions_text

    def test_cmd_runs_after_the_environment_script(
        self,
        tmp_path: Path,
    ) -> None:
        environment_script = tmp_path / "environment.sh"
        environment_script.write_text("export SOME_VERSION=2.0\n")
        versions_text = versions.format_versions_text(
            svn_revision=1,
            version_cmds=['echo "$SOME_VERSION"'],
            environment_script=environment_script,
        )
        assert '$ echo "$SOME_VERSION"\n2.0\n' in versions_text

    def test_failing_cmd_records_its_error_and_exit_code(
        self,
    ) -> None:
        versions_text = versions.format_versions_text(
            svn_revision=1,
            version_cmds=["no-such-compiler --version"],
            environment_script=None,
        )
        assert "no-such-compiler: command not found" in versions_text
        assert "(exit code 127)" in versions_text


## } U-TEST

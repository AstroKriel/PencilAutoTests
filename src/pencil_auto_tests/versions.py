## { MODULE

##
## === DEPENDENCIES
##

## stdlib
import shlex
from pathlib import Path

## personal
from huginn import manage_shell

## local
from pencil_auto_tests import system_layouts

##
## === VERSIONS FILE
## written next to the test report after each run and published with it, so the report says which commit of this
## tool, which Pencil revision, and which compilers and libraries produced it.
##


def _get_tool_commit() -> str:
    """The commit of this clone, with `-dirty` appended when it has local edits."""
    tool_commit = manage_shell.query_cmd_and_capture_output(
        cmd_parts=["git", "describe", "--always", "--dirty"],
        working_directory=system_layouts.PENCIL_AUTO_TESTS_DIR,
        raise_error=False,
    )
    if tool_commit == "":
        return "unknown"
    return tool_commit


def _get_version_cmd_text(
    *,
    version_cmd: str,
    environment_script: Path | None,
) -> str:
    """Run a version command in the environment of the tests; a failing command records its exit code."""
    if environment_script is None:
        shell_script = version_cmd
    else:
        shell_script = f"source {shlex.quote(str(environment_script))} > /dev/null; {version_cmd}"
    cmd_outcome = manage_shell.query_cmd_and_capture_outcome(cmd_parts=["bash", "-c", shell_script])
    cmd_output = (cmd_outcome.stdout + cmd_outcome.stderr).strip()
    cmd_lines = [f"$ {version_cmd}", cmd_output]
    if not cmd_outcome.has_succeeded:
        cmd_lines.append(f"(exit code {cmd_outcome.exit_code})")
    return "\n".join(cmd_lines)


def format_versions_text(
    *,
    svn_revision: int,
    version_cmds: list[str],
    environment_script: Path | None,
) -> str:
    header_lines = [
        f"pencil_auto_tests  {_get_tool_commit()}",
        f"pencil code        r{svn_revision}",
    ]
    version_cmd_texts = [
        _get_version_cmd_text(
            version_cmd=_version_cmd,
            environment_script=environment_script,
        ) for _version_cmd in version_cmds
    ]
    versions_blocks = ["\n".join(header_lines), *version_cmd_texts]
    return "\n\n".join(versions_blocks) + "\n"


## } MODULE

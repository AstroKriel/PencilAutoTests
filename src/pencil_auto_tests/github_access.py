## { MODULE

##
## === DEPENDENCIES
##

## stdlib
import getpass
import re
import socket

## personal
from huginn import manage_log, manage_shell
from ssh_helper import host_keys, ssh_keys

## local
from pencil_auto_tests import system_layouts

##
## === GITHUB
## the fingerprint is published at
## https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints
##

_GITHUB_HOST = "github.com"
_GITHUB_ED25519_FINGERPRINT = "SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU"
_GITHUB_REMOTE_URL_PATTERN = re.compile(
    r"(?:https://github\.com/|git@github\.com:)(?P<repo_path>[\w.-]+/[\w.-]+?)(?:\.git)?/?",
)
DEPLOY_SSH_KEY = ssh_keys.SSHKey(key_name="pencil_auto_tests")
_DEPLOY_SSH_COMMAND = (
    f"ssh -F /dev/null -i {DEPLOY_SSH_KEY.private_key_path} -o IdentitiesOnly=yes -o BatchMode=yes"
)


def get_github_repo_path(
    *,
    remote_url: str,
) -> str:
    """Return `<owner>/<repo>` from a GitHub remote URL over HTTPS or SSH."""
    remote_url_match = _GITHUB_REMOTE_URL_PATTERN.fullmatch(remote_url)
    if remote_url_match is None:
        raise ValueError(f"`{remote_url}` is not a GitHub repository URL")
    return remote_url_match.group("repo_path")


##
## === GIT
##


def _query_git(
    *,
    git_args: list[str],
) -> str:
    return manage_shell.query_cmd_and_capture_output(
        cmd_parts=["git", *git_args],
        working_directory=system_layouts.PENCIL_AUTO_TESTS_DIR,
        raise_error=False,
    )


def _ensure_git_config_value(
    *,
    config_name: str,
    config_value: str,
) -> None:
    current_value = _query_git(git_args=["config", "--local", "--get", config_name])
    if current_value == config_value:
        manage_log.log_note(f"git {config_name} is already `{config_value}`")
        return
    manage_shell.run_cmd_and_show_output(
        cmd_parts=["git", "config", "--local", config_name, config_value],
        working_directory=system_layouts.PENCIL_AUTO_TESTS_DIR,
    )


def get_origin_url() -> str:
    return _query_git(git_args=["remote", "get-url", "origin"])


##
## === PUBLISHING ACCESS
##


def get_machine_name() -> str:
    host_name = socket.gethostname()
    return host_name.split(".")[0]


def ensure_deploy_key_exists() -> None:
    ssh_keys.ensure_key_exists(
        ssh_key=DEPLOY_SSH_KEY,
        purpose="publishing Pencil auto-tests",
        device=get_machine_name(),
        no_passphrase=True,
    )


def ensure_github_trusted() -> None:
    host_keys.ensure_host_trusted(
        host=_GITHUB_HOST,
        expected_fingerprint=_GITHUB_ED25519_FINGERPRINT,
    )


def ensure_git_identity() -> None:
    """Commit as `<account> (<machine>)`, so each commit on GitHub names the machine it came from."""
    account_name = getpass.getuser()
    _ensure_git_config_value(
        config_name="user.name",
        config_value=f"{account_name} ({get_machine_name()})",
    )
    _ensure_git_config_value(
        config_name="user.email",
        config_value=f"{account_name}@{socket.getfqdn()}",
    )


def ensure_ssh_remote(
    *,
    repo_path: str,
) -> None:
    """Fetch and push over SSH with only the deploy key, ignoring any ssh config, and never prompt, so cron runs cannot
    hang."""
    _ensure_git_config_value(
        config_name="remote.origin.url",
        config_value=f"git@{_GITHUB_HOST}:{repo_path}.git",
    )
    _ensure_git_config_value(
        config_name="core.sshCommand",
        config_value=_DEPLOY_SSH_COMMAND,
    )


def has_github_access(
    *,
    repo_path: str,
) -> bool:
    """Whether GitHub accepts the deploy key for the repository; this cannot tell read from write access."""
    exit_code = manage_shell.query_cmd_and_discard_output(
        cmd_parts=[
            "env",
            f"GIT_SSH_COMMAND={_DEPLOY_SSH_COMMAND}",
            "git",
            "ls-remote",
            "--heads",
            f"git@{_GITHUB_HOST}:{repo_path}.git",
        ],
    )
    return exit_code == 0


## } MODULE

## { U-TEST

##
## === DEPENDENCIES
##

## third-party
import pytest

## local
from pencil_auto_tests import github_access

##
## === TEST SUITE
##


class TestGetGitHubRepoPath:

    @pytest.mark.parametrize(
        "remote_url",
        [
            "https://github.com/some-owner/some.repo",
            "https://github.com/some-owner/some.repo.git",
            "https://github.com/some-owner/some.repo/",
            "git@github.com:some-owner/some.repo.git",
        ],
    )
    def test_https_and_ssh_urls_give_the_repo_path(
        self,
        remote_url: str,
    ) -> None:
        assert github_access.get_github_repo_path(remote_url=remote_url) == "some-owner/some.repo"

    @pytest.mark.parametrize(
        "remote_url",
        [
            "https://gitlab.com/some-owner/some-repo.git",
            "https://github.com/some-owner",
            "",
        ],
    )
    def test_other_urls_are_refused(
        self,
        remote_url: str,
    ) -> None:
        with pytest.raises(ValueError, match="not a GitHub repository URL"):
            github_access.get_github_repo_path(remote_url=remote_url)


## } U-TEST

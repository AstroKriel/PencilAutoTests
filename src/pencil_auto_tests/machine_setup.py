## { MODULE

##
## === DEPENDENCIES
##

## stdlib
import shutil
from dataclasses import dataclass

##
## === REQUIREMENTS
## the tools every machine needs, whatever the system; the compilers and MPI depend on the Pencil configs named in
## each system config, so `pc_auto-test` reports those itself.
##

PENCIL_SVN_TRUNK_URL = "https://pencil-code.org/svn/trunk/"


@dataclass(frozen=True)
class RequiredTool:
    name: str
    reason: str


REQUIRED_TOOLS = (
    RequiredTool(
        name="svn",
        reason=
        "checks out and updates the Pencil code; run-test.sh only runs tests when `svn up` finds new commits",
    ),
    RequiredTool(
        name="perl",
        reason="pencil-test and pc_auto-test, which run the tests, are Perl scripts",
    ),
    RequiredTool(
        name="make",
        reason="pc_build compiles each sample with make",
    ),
    RequiredTool(
        name="wget",
        reason=
        "pc_auto-test looks up the git commit for the svn revision; without it the test report records no commit",
    ),
    RequiredTool(
        name="git",
        reason="publishes the summaries and the test report to this repository on GitHub",
    ),
)


def get_missing_tools() -> list[RequiredTool]:
    return [_required_tool for _required_tool in REQUIRED_TOOLS if shutil.which(_required_tool.name) is None]


## } MODULE

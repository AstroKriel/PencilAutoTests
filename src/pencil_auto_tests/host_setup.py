## { MODULE

##
## === DEPENDENCIES
##

## stdlib
import shutil

##
## === REQUIREMENTS
## the tools every test needs, whatever its compiler; the compilers and MPI depend on the configs in the settings
## file, so `pc_auto-test` reports those itself.
##

PENCIL_SVN_TRUNK_URL = "https://pencil-code.org/svn/trunk/"
REQUIRED_TOOLS = [
    "svn",
    "perl",
    "make",
    "wget",
    "git",
]


def find_missing_tools() -> list[str]:
    return [
        _tool_name
        for _tool_name in REQUIRED_TOOLS
        if shutil.which(_tool_name) is None
    ]


## } MODULE

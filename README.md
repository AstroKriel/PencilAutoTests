# PencilAutoTests

Set up, run, and publish [Pencil Code](https://pencil-code.org) auto-tests on any machine.

Pencil ships its own nightly-test scripts: `run-test.sh` updates an svn checkout of trunk and, when there are new commits, runs the tests with `pencil-test`. Each machine still has to be set up by hand, with paths and options edited into the script and results published from a web server. This repository wraps those scripts so that each setup is described by one system config, set up and run with one command each, and publishes its results to GitHub: a short test summary per run on `main`, and the latest test logs and test report on GitHub Pages.

This README is also the setup guide. It is built up as each step is checked, so it covers only what works so far.

## Terms

| Term | Meaning |
|---|---|
| machine | The computer the tests run on |
| system | One configured setup on a machine: where Pencil is checked out, where its logs go, which levels run, and which compiler configs build them. One machine can host several systems, for example one with Intel and one with GNU |
| system config | The file describing a system, `system_configs/<system-name>.toml` |

Pencil uses its own words in places, such as "test" for a checked sample and "config" for its compiler configuration files. Values passed to Pencil keep Pencil's spelling.

## How it works

| Command | Does |
|---|---|
| `setup --system-name <system-name>` | Checks the required tools, creates the system directories, and checks out trunk |
| `run --system-name <system-name>` | Calls `run-test.sh`, which tests only if `svn up` finds new commits, and, if tests ran, writes the summary and publishes it |
| `publish --system-name <system-name>` | Summarises and publishes the latest test report again, for example after a failed push |
| `write-summary --system-name <system-name>` | Writes the test summary of the latest test report, without running or publishing anything |

The system name is the unique id of a system, and its system config is the file of the same name: `--system-name laptop-trial` loads `system_configs/laptop-trial.toml`.

`run-test.sh` is kept in `scripts/`, copied from `utils/cronjobs/` in the Pencil Code. The only change is that its settings can be set from the environment, which `run` uses to pass the system config through; without them it behaves as upstream. The header of the copy lists the variables. The script calls the system name its `TEST`.

## System configs

Everything about how a system runs is in its system config, so nothing has to be remembered at run time and every change is versioned. A system belongs to one machine. A system config answers four questions; paths may start with `~`.

| Key | Question |
|---|---|
| `pencil_code_dir` | Where should the Pencil code be checked out? The samples are also built and run inside it, so use a local disk with room for the builds |
| `test_logs_dir` | Where should the test logs go? `pencil-test` writes the latest logs of this system, and the report summarising them, to `<test-logs-dir>/<system-name>/`, and keeps the run before in `<system-name>-previous/` |
| `test_levels` | Which test levels should run? Such as `"0"`, `"0,1"`, or `"2-3"`; the levels are described above `%tests` in `bin/pc_auto-test` |
| `pencil_build_configs` | Which Pencil build configs should the samples be built with? Names of the files `pc_build` reads from `config/` in the Pencil code, such as `GNU-GCC_MPI` |

For example:

```toml
pencil_code_dir = "~/pencil-auto-tests/pencil-code"
test_logs_dir = "~/pencil-auto-tests/test-logs"
test_levels = "0"
pencil_build_configs = [
    "GNU-GCC_MPI",
    "GNU-GCC_debug",
]
```

`run` always adds the `pc_auto-test` options `--auto-clean`, `--bisect`, and `--local-lock`.

## Results

Each system has its own folder in `test_history/`. Each run adds one test summary there, named by the date the run started and the svn revision it tested, and copies it to `latest.txt`:

```text
test_history/
└── <system-name>/
    ├── latest.txt  # copy of the newest test summary
    └── 2026-11-10_r46257.txt
```

A test summary condenses the test report of one run to one line per test, in the order the tests ran:

```text
no-modules    failed validating results
most-modules  ok
```

A test is `ok`, `failed <phase>` with the first phase that failed, or `unfinished` if it stopped before its results were validated. `diff` between two files shows which tests changed, and the two revisions bracket the commits that changed them.

The latest test report of each system, as `pencil-test` writes it, is served with its test logs by GitHub Pages at `https://<owner>.github.io/<repository>/<system-name>/`.

## Setup

### Requirements

`svn`, `perl`, `make`, `wget`, and `git`, which `setup` checks, plus the compilers and MPI that the chosen `--config-files` need. Without `wget` the tests still run, but `pc_auto-test` cannot look up the git commit for the svn revision. Python and the other dependencies come through [`uv`](https://docs.astral.sh/uv/).

### Install

Fork or clone this repository; publishing pushes to its `origin`, so a fork publishes to its own repository and Pages address.

```bash
git clone <repository-url>
cd PencilAutoTests
uv sync
```

### Set up a system

Write `system_configs/<system-name>.toml`, then:

```bash
.venv/bin/pencil_auto_tests setup --system-name <system-name>
```

`setup` is safe to repeat: it creates only what is missing and never checks out trunk over an existing checkout.

### Run

```bash
.venv/bin/pencil_auto_tests run --system-name <system-name>
```

`run` calls `run-test.sh`, which updates the checkout with `svn up` and runs the tests only if trunk has new commits. Upstream, `run-test.sh` also waits for a trigger file, which Nordita fills from a GitHub webhook; here it is meant to be called on a schedule, so `run` turns the trigger off and `svn up` alone decides. To run without new commits, delete `<pencil-code-dir>/README.md` first; `svn up` restores it, and `run-test.sh` counts that as an update.

### Publishing

After tests ran, `run` publishes in two places:

- `main`: it commits `test_history/<system-name>/`, pulls with rebase, and pushes. It refuses to start if the branch already holds commits that are not pushed, so it only ever pushes its own commit.
- `gh-pages`: it replaces the folder `<system-name>/` with the latest test logs and report from `<test-logs-dir>/<system-name>/` and keeps the folders of other systems. The branch is rebuilt as a single commit each time, so bulk logs never pile up in history, and the push is refused if another machine pushed in between.

GitHub enables Pages on its own once a branch named `gh-pages` exists.

## Systems in this repository

| System | Machine | Use |
|---|---|---|
| `laptop-trial` | a laptop | Development, with the GNU configs |

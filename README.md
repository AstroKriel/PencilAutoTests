# PencilAutoTests

Set up, run, and publish [Pencil Code](https://pencil-code.org) auto-tests on any machine.

Pencil ships its own nightly-test scripts: `run-test.sh` updates an svn checkout of trunk and, when there are new commits, runs the tests with `pencil-test`. Each test host still has to be set up by hand, with paths and options edited into the script and results published from a web server. This repository wraps those scripts so that a test host is described by one settings file, set up and run with one command each, and publishes its results to GitHub: a short summary per run on `main`, and the full results page on GitHub Pages.

This README is also the setup guide. It is built up as each step is checked, so it covers only what works so far.

## How it works

| Command | Does |
|---|---|
| `setup --test <test-name>` | Checks the required tools, creates the test directories from the settings file, and checks out trunk |
| `run --test <test-name>` | Fills the trigger file, calls `run-test.sh`, and, if tests ran, writes the summary and publishes it |
| `publish --test <test-name>` | Summarises and publishes the latest results page again, for example after a failed push |
| `write-summary --test <test-name>` | Writes the summary of the latest results page, without running or publishing anything |

`run-test.sh` is kept in `src/pencil_auto_tests/upstream/`, copied from `utils/cronjobs/` in the Pencil Code. The only change is that its settings can be set from the environment, which `run` uses to pass the settings file through; without them it behaves as upstream. The header of the copy lists the variables.

## Settings

Everything about how a test runs is in `systems/<test-name>.toml`, so nothing has to be remembered at run time and every change is versioned. A test name belongs to one machine.

| Setting | Meaning |
|---|---|
| `test_root` | Directory holding the svn checkout `<test-name>/` and the trigger folder `UPDATE/`; `~` is expanded. Use a local disk with room for the builds |
| `results_dir` | Directory that `pencil-test` writes `<test-name>/` results into |
| `levels` | Test levels to run, such as `"0"`, `"0,1"`, or `"2-3"`; the levels are described above `%tests` in `bin/pc_auto-test` |
| `auto_test_options` | `pc_auto-test` options after `--level`, one per entry, such as the `--config-files` |

For example:

```toml
test_root = "~/pencil-auto-tests"
results_dir = "~/pencil-auto-tests/results"
levels = "0"
auto_test_options = [
    "--config-files=GNU-GCC_MPI+GNU-GCC_debug",
    "--auto-clean",
    "--bisect",
    "--local-lock",
]
```

## Results

Each test name has its own folder in `runs/`. Each run adds one file there, named by the date the run started and the svn revision it tested, and copies it to `latest.txt`:

```text
runs/
└── <test-name>/
    ├── latest.txt  # copy of the newest run
    └── 2026-11-10_r46257.txt
```

Each file has one line per test, in the order the tests ran:

```text
no-modules    failed validating results
most-modules  ok
```

A test is `ok`, `failed <phase>` with the first phase that failed, or `unfinished` if it stopped before its results were validated. `diff` between two files shows which tests changed, and the two revisions bracket the commits that changed them.

The full results page of each test, as `pencil-test` writes it, is served by GitHub Pages at `https://<owner>.github.io/<repository>/<test-name>/`.

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

### Set up a test

Write `systems/<test-name>.toml`, then:

```bash
.venv/bin/pencil_auto_tests setup --test <test-name>
```

`setup` is safe to repeat: it creates only what is missing and never checks out trunk over an existing checkout.

### Run

```bash
.venv/bin/pencil_auto_tests run --test <test-name>
```

`run` fills the trigger file and calls `run-test.sh`, which updates the checkout with `svn up` and runs the tests only if trunk has new commits. To run without new commits, delete `<test-root>/<test-name>/README.md` first; `svn up` restores it, and `run-test.sh` counts that as an update.

### Publishing

After tests ran, `run` publishes in two places:

- `main`: it commits `runs/<test-name>/`, pulls with rebase, and pushes. It refuses to start if the branch already holds commits that are not pushed, so it only ever pushes its own commit.
- `gh-pages`: it replaces the folder `<test-name>/` with the full results from `<results-dir>/<test-name>/` and keeps the folders of other tests. The branch is rebuilt as a single commit each time, so bulk logs never pile up in history, and the push is refused if another host pushed in between.

GitHub enables Pages on its own once a branch named `gh-pages` exists.

## Tests in this repository

| Test name | Machine | Use |
|---|---|---|
| `laptop-trial` | a laptop | Development, with the GNU configs |

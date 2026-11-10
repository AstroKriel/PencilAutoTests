# PencilAutoTests

Scripts that run [Pencil Code](https://pencil-code.org) auto-tests at AIfA Bonn and publish the results here. The main test, `intel-bonn`, runs the Intel compiler on CPU only, which the existing Pencil test hosts do not cover.

This README is also the setup guide. It is built up stage by stage as each step is checked, so it covers only what works so far.

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

## Settings

Everything about how a test runs is in `systems/<test-name>.toml`, so nothing has to be remembered at run time and every change is versioned. A test name belongs to one machine.

| Setting | Meaning |
|---|---|
| `test_root` | Directory holding the svn checkout `<test-name>/` and the trigger folder `UPDATE/`; `~` is expanded |
| `results_dir` | Directory that `pencil-test` writes `<test-name>/` results into |
| `levels` | Test levels to run, such as `"0"`, `"0,1"`, or `"2-3"` |
| `auto_test_options` | `pc_auto-test` options after `--level`, one per entry, such as the `--config-files` |

| Test name | Machine | Use |
|---|---|---|
| `laptop-trial` | laptop | Development, with the GNU configs; removed once the office PC runs `intel-bonn` |

## Setup

### Requirements

`svn`, `perl`, `make`, `gfortran`, an MPI (`mpif90`, `mpirun`), and `wget`. Without `wget` the tests still run, but `pc_auto-test` cannot look up the git commit for the svn revision. Python and the other dependencies come through [`uv`](https://docs.astral.sh/uv/).

### Test directories

The test name ties three places together, and all three must match. Create them before the first run, with `<test-root>` and `<results-dir>` as in the settings file:

```bash
mkdir -p <test-root>/UPDATE <results-dir>/<test-name>
cd <test-root>
svn checkout -q https://pencil-code.org/svn/trunk/ <test-name>
```

If `<results-dir>/<test-name>/` is missing, upstream `run-test.sh` empties the trigger file and runs nothing; the only trace is an error in its output. `pencil_auto_tests run` checks for all three first.

### This repository

```bash
git clone https://github.com/AstroKriel/PencilAutoTests.git
cd PencilAutoTests
uv sync
```

Run the tests once by hand:

```bash
.venv/bin/pencil_auto_tests run --test <test-name>
```

`run` fills the trigger file and calls `run-test.sh`, which updates the checkout with `svn up` and runs the tests only if trunk has new commits. If a new results page appears, `run` writes the dated summary into `runs/<test-name>/`. To run without new commits, delete `<test-root>/<test-name>/README.md` first; `svn up` restores it, and `run-test.sh` counts that as an update.

`run-test.sh` is kept in `src/pencil_auto_tests/upstream/`, copied from `utils/cronjobs/` in the Pencil Code. The only change is that its settings can be set from the environment, which `run` uses to pass the settings file through; without them it behaves as upstream. The header of the copy lists the variables.

To summarise the latest results page again without running anything:

```bash
.venv/bin/pencil_auto_tests write-summary --test <test-name>
```

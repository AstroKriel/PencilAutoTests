# PencilAutoTests

Scripts that run the `intel-bonn` [Pencil Code](https://pencil-code.org) auto-tests at AIfA Bonn and publish the results here. The test runs the Intel compiler on CPU only, which the existing Pencil test hosts do not cover.

This README is also the setup guide. It is built up stage by stage as each step is checked, so it covers only what works so far.

## Results

Each run adds one file to `runs/`, named by the date the run started and the svn revision it tested, and copies it to `runs/latest.txt`:

```text
runs/
├── latest.txt  # copy of the newest run
└── 2026-11-10_r46255.txt
```

Each file has one line per test, in the order the tests ran:

```text
no-modules    failed validating results
most-modules  ok
```

A test is `ok`, `failed <phase>` with the first phase that failed, or `unfinished` if it stopped before its results were validated. `diff` between two files shows which tests changed, and the two revisions bracket the commits that changed them.

## Setup

### Requirements

`svn`, `perl`, `make`, `gfortran`, an MPI (`mpif90`, `mpirun`), and `wget`. Without `wget` the tests still run, but `pc_auto-test` cannot look up the git commit for the svn revision. Python and the other dependencies come through [`uv`](https://docs.astral.sh/uv/).

### Layout

One test name ties three places together, and all three must match:

```text
<test-root>/intel-bonn/  # svn checkout of trunk
<test-root>/UPDATE/intel-bonn  # trigger file; a run happens only when it is not empty
<results-dir>/intel-bonn/  # pencil-test output: index.html, result.svg, per-test logs
```

Create all three before the first run:

```bash
mkdir -p <test-root>/UPDATE <results-dir>/intel-bonn
touch <test-root>/UPDATE/intel-bonn
cd <test-root>
svn checkout -q https://pencil-code.org/svn/trunk/ intel-bonn
```

If `<results-dir>/intel-bonn/` is missing, `run-test.sh` empties the trigger file and runs nothing; the only trace is an error in its output.

### This repository

```bash
git clone https://github.com/AstroKriel/PencilAutoTests.git
cd PencilAutoTests
uv sync
```

Turn a results page into a dated summary:

```bash
.venv/bin/pencil_auto_tests write-summary --results-page <results-dir>/intel-bonn/index.html --runs-dir runs
```

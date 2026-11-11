# PencilAutoTests

Nightly [Pencil Code](https://pencil-code.org) auto-tests on any machine, set up from one config file, with results published to GitHub.

- Latest test report of each system: `https://astrokriel.github.io/PencilAutoTests/<system-name>/`
- Every run, one line per sample: `test_history/<system-name>/`

```text
no-modules    failed validating results
most-modules  ok
```

## Setting up a machine

1. Install `svn`, `perl`, `make`, `wget`, `git`, [`uv`](https://docs.astral.sh/uv/), and the compilers and MPI that your build configs need.
2. Clone this repository and install it:

   ```bash
   git clone <repository-url>
   cd PencilAutoTests
   uv sync
   ```

3. Describe the system in `system_configs/<system-name>.toml`:

   ```toml
   pencil_code_dir = "/data/pencil/intel-bonn"    # where Pencil is checked out, built, and run
   test_logs_dir = "/data/pencil/test-logs"       # where pencil-test writes the test report and logs
   test_levels = "0-3"                            # levels from the %tests table in bin/pc_auto-test
   pencil_build_configs = ["Intel_MPI-mpiifx"]    # config files read by pc_build
   environment_script = "~/intel/oneapi/setvars.sh"  # optional: sourced first, e.g. for oneAPI
   ```

4. Check the tools, create the directories, and check out trunk:

   ```bash
   .venv/bin/pencil_auto_tests setup --system-name <system-name>
   ```

5. Run it nightly from `cron`:

   ```text
   30 2 * * *  <repository>/.venv/bin/pencil_auto_tests run --system-name <system-name>
   ```

To summarise or publish the latest test report again, for example after a failed push, use `write-test-summary` or `publish` with the same `--system-name`.

## How it relates to the Pencil scripts

- `scripts/run-test.sh` is a copy of `utils/cronjobs/run-test.sh`, changed only to read its settings from the environment and to run without a trigger file. Its header lists the changes.
- `run` tests only when `svn up` finds new commits. It then pushes the one-line-per-sample summary to `main`, and the latest test report and logs to `gh-pages`, in a folder per system, to the repository it was cloned from.

## Systems

| System | Machine | Build configs |
|---|---|---|
| `laptop-trial` | a laptop | `GNU-GCC_MPI`, `GNU-GCC_debug` |

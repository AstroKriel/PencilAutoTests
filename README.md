# PencilAutoTests

Nightly [Pencil Code](https://pencil-code.org) auto-tests on any machine, set up from one config file, with results published to GitHub.

- Latest test report of each system: `https://astrokriel.github.io/PencilAutoTests/<system-name>/`
- Every run, one line per sample: `test_history/<system-name>/`

## Example

`system_configs/example.toml` runs levels 0 and 1 with gfortran and OpenMPI, so it works on most Linux machines (see the requirements below). It checks out Pencil under `~/pencil-auto-tests/example/`, and `--no-publish` keeps the results local:

```bash
git clone https://github.com/AstroKriel/PencilAutoTests.git
cd PencilAutoTests
uv sync
.venv/bin/pencil_auto_tests setup --system-name example
.venv/bin/pencil_auto_tests run --system-name example --no-publish
cat test_history/example/latest.txt
```

The run takes about eight minutes, most of it compiling, and writes one line per sample. In the best case, every sample passes:

```text
no-modules                    ok
most-modules                  ok
backwards-compatible          ok
1d-tests/implicit_diffusion   ok
2d-tests/chemistry_GrayScott  ok
2d-tests/shearwave-dust-par   ok
dust-vortex                   ok
damped_alfven_waves           ok
corona                        ok
helical-MHDturb               ok
```

Otherwise, a line names the first step that failed, in the words of `pc_auto-test`:

| Line | Meaning |
|---|---|
| `failed compiling` | the sample did not build |
| `failed starting` | `start.x` stopped while setting up the initial conditions |
| `failed running` | `run.x` stopped during the simulation |
| `failed validating results` | everything ran, but the output differs from the reference files of the sample |
| `unfinished` | stopped before validation without a failed step, for example at the time limit |

The reason is in the full test report, with the build, start, and run logs of each sample: `~/pencil-auto-tests/example/test-logs/example/index.html` for the example. A [dated test report of the example](https://astrokriel.github.io/PencilAutoTests/example/) is published to show what one looks like.

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
   test_levels = "0-3"                            # a level or range from the %tests table in bin/pc_auto-test
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

`run` tests only when `svn up` finds new commits, except on the first run of a system, and then pushes the test summary to `main` and the latest test report and logs to `gh-pages` of the repository it was cloned from. Add `--no-publish` to try a system without pushing. To summarise or publish the latest test report again, for example after a failed push, use `write-test-summary` or `publish` with the same `--system-name`.

## File structure

```text
PencilAutoTests/
├── src/
│   └── pencil_auto_tests/
│       ├── user_interface.py  # [entrypoint] the command table and main()
│       ├── system_configs.py  # loads system_configs/<system-name>.toml
│       ├── system_layouts.py  # every path of a system, on the machine and in this repository
│       ├── required_tools.py  # tools every machine needs, and why
│       ├── test_reports.py  # reads the test report that pencil-test writes
│       ├── test_summaries.py  # writes the one-line-per-sample test summaries
│       └── publish_to_github.py  # pushes test summaries to main and test reports to gh-pages
├── scripts/
│   └── run-test.sh  # copy of utils/cronjobs/run-test.sh; reads its settings from the environment, runs without a trigger file
├── system_configs/  # one file per system; example.toml runs on most machines
├── test_history/  # dated test summaries of each system, plus latest.txt
├── utests/  # unit tests; data/ holds two real test reports
├── pyproject.toml  # package metadata; registers the pencil_auto_tests command
├── uv.lock  # pinned dependency versions
├── .gitignore
└── README.md
```

---

## License

This project is licensed under the MIT License; see the [LICENSE](./LICENSE) file for details.

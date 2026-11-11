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
├── system_configs/  # one file per system
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

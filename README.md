# PencilAutoTests

Nightly [Pencil Code](https://pencil-code.org) auto-tests on any machine, set up from one config file, with results published to GitHub.

- Latest test report of each system: `https://astrokriel.github.io/PencilAutoTests/<system-name>/`
- The commit of this tool, the Pencil revision, and the compiler and library versions of that run: `https://astrokriel.github.io/PencilAutoTests/<system-name>/versions.txt`
- Every run, one line per sample: `test_history/<system-name>/`

## Example

`system_configs/example.toml` runs levels 0 and 1 with gfortran and OpenMPI, so it works on most Linux machines (see the requirements below). It checks out Pencil under `~/pencil-auto-tests/example/`, and `--no-publish` keeps the results local:

```bash
git clone https://github.com/AstroKriel/PencilAutoTests.git
cd PencilAutoTests
uv run pencil_auto_tests setup --system-name example
uv run pencil_auto_tests run --system-name example --no-publish
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

1. Install `svn`, `perl`, `make`, `wget`, `git`, `cron`, [`uv`](https://docs.astral.sh/uv/), and the compilers and MPI that your build configs need. For the Intel build configs, `scripts/install-intel-oneapi.sh <install-dir> <download-dir>` installs the Intel compilers and MPI without root, and `scripts/install-hdf5-intel.sh <install-dir> <download-dir>` builds HDF5 with them, for the samples that use HDF5; an HDF5 built with gfortran, as packaged by Linux distributions, does not work with the Intel compilers.
2. Clone this repository:

   ```bash
   git clone <repository-url>
   cd PencilAutoTests
   ```

3. Describe the system in `system_configs/<system-name>.toml`. Name systems `<site>-<toolchain>`, e.g. `bonn-intel`, so systems at one site sort together:

   ```toml
   pencil_code_dir = "/data/pencil/bonn-intel"  # where Pencil is checked out, built, and run
   test_logs_dir = "/data/pencil/test-logs"  # where pencil-test writes the test report and logs
   test_levels = "0-3"  # a level or range from the %tests table in bin/pc_auto-test
   pencil_build_configs = ["Intel_MPI-mpiifx"]  # config files read by pc_build
   environment_script = "~/intel/oneapi/setvars.sh"  # optional: sourced first, e.g. for oneAPI
   version_cmds = ["ifx --version"]  # optional: their output goes into versions.txt
   ```

   When the environment needs more than one script, write a small one next to the system config that sources the others, as `system_configs/bonn-intel.sh` does for oneAPI and HDF5.

4. Check the tools, create the directories, and check out trunk; `uv run` also installs the tool into `.venv/`:

   ```bash
   uv run pencil_auto_tests setup --system-name <system-name>
   ```

5. Give this clone push access to GitHub. The first call creates the deploy key `~/.ssh/id_ed25519_pencil_auto_tests` and prints its public key; add it under Settings → Deploy keys of the repository, with write access, then call it again:

   ```bash
   uv run pencil_auto_tests setup-publishing
   ```

   It checks the host key of GitHub against the published fingerprint, then sets a git identity naming the account and machine, and makes this clone push over SSH with only the deploy key.

6. Schedule it. This adds two lines to the `crontab` of the account: one runs the tests nightly at 02:30 with the installed command, so a nightly run never resolves or downloads anything; the other kills test processes older than three hours. Each line ends in `# pencil_auto_tests:<system-name>`, so scheduling again replaces them and leaves other lines alone:

   ```bash
   uv run pencil_auto_tests schedule --system-name <system-name>
   ```

`run` tests only when `svn up` finds new commits, except on the first run of a system, and then pushes the test summary to `main` and the latest and previous test reports and logs to `gh-pages` of the repository it was cloned from. Add `--no-publish` to try a system without pushing. To summarise or publish the latest test report again, for example after a failed push, use `write-test-summary` or `publish` with the same `--system-name`.

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
│       ├── versions.py  # writes versions.txt next to the test report
│       ├── publish_to_github.py  # pushes test summaries to main and test reports to gh-pages
│       ├── github_access.py  # deploy key, GitHub host key, git identity, and SSH remote of this clone
│       └── cron_schedules.py  # the cron lines of each system
├── scripts/
│   ├── run-test.sh  # copy of utils/cronjobs/run-test.sh; reads its settings from the environment, runs without a trigger file
│   ├── install-intel-oneapi.sh  # installs the Intel compilers and MPI without root
│   └── install-hdf5-intel.sh  # builds HDF5 with the Intel compilers and MPI without root
├── system_configs/  # one config per system, plus its environment script if it needs one; example.toml runs on most machines
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

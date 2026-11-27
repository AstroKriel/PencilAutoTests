#!/usr/bin/env bash
# Install the Intel Fortran and C compilers and Intel MPI, without root, for the Intel Pencil build configs.
# Usage: install-intel-oneapi.sh <install-dir> <download-dir>
# Then set `environment_script = "<install-dir>/setvars.sh"` in the system config.

set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <install-dir> <download-dir>" >&2
    exit 1
fi
install_dir=$1
download_dir=$2

installer_url="https://registrationcenter-download.intel.com/akdlm/IRC_NAS/902d3dfc-ece4-4282-9a4a-48020ca454e6/intel-oneapi-toolkit-2026.2.0.667_offline.sh"
installer_path="$download_dir/$(basename "$installer_url")"
components="intel.oneapi.lin.ifort-compiler:intel.oneapi.lin.dpcpp-cpp-compiler:intel.oneapi.lin.mpi.devel"

mkdir -p "$download_dir"
wget --continue --directory-prefix="$download_dir" "$installer_url"
sh "$installer_path" -r yes -a --silent \
    --eula accept \
    --intel-sw-improvement-program-consent decline \
    --components "$components" \
    --install-dir "$install_dir"

echo "installed; set environment_script = \"$install_dir/setvars.sh\" in the system config"

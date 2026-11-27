#!/usr/bin/env bash
# Build parallel HDF5 with the Intel compilers and Intel MPI, without root, for the samples that use HDF5.
# Usage: install-hdf5-intel.sh <install-dir> <download-dir>, after sourcing the setvars.sh of oneAPI.
# Then put <install-dir>/bin first on PATH and <install-dir>/lib on LD_LIBRARY_PATH in the environment script of the
# system, e.g. system_configs/bonn-intel.sh.

set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <install-dir> <download-dir>" >&2
    exit 1
fi
install_dir=$1
download_dir=$2

if ! command -v mpiifx > /dev/null || ! command -v mpiicx > /dev/null; then
    echo "mpiifx and mpiicx not found; source the setvars.sh of oneAPI first" >&2
    exit 1
fi

source_url="https://github.com/HDFGroup/hdf5/releases/download/hdf5_1.14.6/hdf5-1.14.6.tar.gz"
source_path="$download_dir/$(basename "$source_url")"
source_dir="$download_dir/hdf5-1.14.6"

mkdir -p "$download_dir"
wget --continue --directory-prefix="$download_dir" "$source_url"
tar -xf "$source_path" -C "$download_dir"
cd "$source_dir"
CC=mpiicx FC=mpiifx ./configure --prefix="$install_dir" --enable-parallel --enable-fortran
make -j "$(nproc)"
make install

echo "installed; put $install_dir/bin first on PATH and $install_dir/lib on LD_LIBRARY_PATH in the environment script"

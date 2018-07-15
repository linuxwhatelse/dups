#!/usr/bin/env bash

cd "$(dirname "$0")"

PKG_DIR=$(pwd)

# Navigate to project root
cd "$(realpath ../../../)"

python3 setup.py --command-packages=stdeb.command \
    sdist_dsc --dist-dir ${PKG_DIR} \
    bdist_deb

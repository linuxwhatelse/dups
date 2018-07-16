#!/usr/bin/env bash

cd "$(dirname "$0")"

if [ $# -lt 1 ]; then
    echo "usage: $0 [RELEASE_FILE]"
    exit 1
fi

RELEASE_FILE="$1"

PKG_DIR="$(pwd)"

# Navigate to project root
cd "$(realpath ../../../)"

python3 setup.py --command-packages=stdeb.command \
    sdist_dsc --dist-dir ${PKG_DIR} \
    bdist_deb

cd "${PKG_DIR}"
mv *.deb "${RELEASE_FILE}"

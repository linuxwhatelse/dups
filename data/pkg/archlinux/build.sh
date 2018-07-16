#!/usr/bin/env bash

cd "$(dirname "$0")"

if [ $# -lt 1 ]; then
    echo "usage: $0 [RELEASE_FILE]"
    exit 1
fi

RELEASE_FILE="$1"

SRC_DIR="$(realpath ../../../)"

mkdir -p src
ln -s "${SRC_DIR}" "./src/python-dups"

chown -R nobody.nobody "${SRC_DIR}"
sudo -u nobody makepkg --noextract

mv *.pkg.tar.xz "${RELEASE_FILE}"

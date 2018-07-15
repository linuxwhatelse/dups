#!/usr/bin/env bash

cd "$(dirname "$0")"

TARGET_DIR=$(pwd)

# We can't build in /root so we have make a copy
BUILD_DIR="/tmp/dups-build"
cp -r "$(realpath ../../../)" "${BUILD_DIR}"

cd "${BUILD_DIR}/data/pkg/archlinux"
mkdir -p src && ln -s "${BUILD_DIR}" "./src/python-dups"

chown -R nobody.nobody "${BUILD_DIR}"

sudo -u nobody makepkg --noextract

cp *.pkg.tar.xz "${TARGET_DIR}"

#!/usr/bin/env bash

if [ $# -lt 2 ]; then
    echo "usage: $0 [PKG_DIR] [RELEASE_FILE]"
    exit 1
fi

PKG_DIR="$1"
RELEASE_FILE="$2"

cp -r /dups /tmp/dups
cd /tmp/dups

${PKG_DIR}/build.sh ${RELEASE_FILE}

# Check if the built file exists
ls ${RELEASE_FILE}

#!/usr/bin/env bash

cd "$(dirname "$0")"

if [ $# -lt 1 ]; then
    echo "usage: $0 [RELEASE_FILE]"
    exit 1
fi

RELEASE_FILE="$1"

dpkg -i ${RELEASE_FILE}

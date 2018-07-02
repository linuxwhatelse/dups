#!/usr/bin/env bash

if [ $# -lt 1 ]; then
    echo "usage: $0 [PIP]"
    exit 1
fi

PIP="$1"

cp -r /dups /root/dups
cd /root/dups

export INCLUDE_DATA_FILES=True
${PIP} install .

# Check if dups command is available
dups --help

# Check if systemd user service was installed
ls /usr/lib/systemd/user/dups.service


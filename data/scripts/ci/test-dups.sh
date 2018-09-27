#!/usr/bin/env bash

if [ $# -lt 1 ]; then
    echo "usage: $0 [PYTHON]"
    exit 1
fi

PYTHON="$1"

cp -r /dups /home/dups/source
chown -R dups:dups /home/dups/source

# SSH server is required for remote tests
/usr/sbin/sshd

# Run all unittests
cd /home/dups/source
su dups -c "${PYTHON} -m pytest -vv tests"

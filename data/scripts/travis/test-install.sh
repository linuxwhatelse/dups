#!/usr/bin/env bash

if [ $# -lt 1 ]; then
    echo "usage: $0 [PIP]"
    exit 1
fi

PIP="$1"

cp -r /dups /root/dups
cd /root/dups

export INCLUDE_DATA_FILES='systemd dbus'
${PIP} install .

# Check if dups command is available
dups --help

# Check if system files where installed
ls /usr/lib/systemd/user/dups.service
ls /usr/lib/systemd/system/dups@.service

ls /etc/dbus-1/system.d/de.linuxwhatelse.dups.conf

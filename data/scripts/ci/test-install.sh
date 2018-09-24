#!/usr/bin/env bash

if [ $# -lt 2 ]; then
    echo "usage: $0 [PKG_DIR] [RELEASE_FILE]"
    exit 1
fi

PKG_DIR="$1"
RELEASE_FILE="$2"

cp -r /dups /tmp/dups
cd /tmp/dups

${PKG_DIR}/install.sh ${RELEASE_FILE}

# Check if dups command is available
dups --help

# Check if system files where installed
ls /usr/lib/systemd/user/dups.service
ls /usr/lib/systemd/system/dups@.service

ls /etc/dbus-1/system.d/de.linuxwhatelse.dups.daemon.conf

ls /usr/share/applications/de.linuxwhatelse.dups.desktop

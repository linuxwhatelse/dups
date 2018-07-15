#!/usr/bin/env bash

if [ $# -lt 1 ]; then
    echo "usage: $0 [PKG_DIR]"
    exit 1
fi

PKG_DIR="$1"

cp -r /dups /root/dups
cd /root/dups

${PKG_DIR}/build.sh
${PKG_DIR}/install.sh

# Check if dups command is available
dups --help

# Check if system files where installed
ls /usr/lib/systemd/user/dups.service
ls /usr/lib/systemd/system/dups@.service

ls /etc/dbus-1/system.d/de.linuxwhatelse.dups.conf

ls /usr/share/applications/de.linuxwhatelse.dups.desktop

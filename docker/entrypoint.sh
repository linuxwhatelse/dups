#!/usr/bin/env sh

if [ ! -z "$BACKUP_SCHEDULE" ] && [ ! -z "$BACKUP_COMMAND" ]; then
    echo "${BACKUP_SCHEDULE} ${BACKUP_COMMAND}" > /etc/crontabs/root
fi

if [ ! -z "$PRUNE_SCHEDULE" ] && [ ! -z "$PRUNE_COMMAND" ]; then
    echo "${PRUNE_SCHEDULE} ${PRUNE_COMMAND}" >> /etc/crontabs/root
fi

/usr/sbin/crond -l 8 -f

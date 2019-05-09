FROM alpine:latest

ENV BACKUP_SCHEDULE='0 0 * * *' \
    BACKUP_COMMAND='dups backup' \
    PRUNE_SCHEDULE='0 1 * * *' \
    PRUNE_COMMAND='dups rm -y --gffs'

RUN apk add --no-cache \
    rsync \
    python3 \
    py3-paramiko

# Installing ruamel.yaml through the official repo is pretty much impossible
RUN pip3 install --no-cache-dir ruamel.yaml

RUN mkdir -p /tmp/dups \
    && cd /tmp/dups \
    && wget https://github.com/linuxwhatelse/dups/archive/master.zip \
    && unzip master.zip \
    && cd dups-master \
    && pip3 install --no-deps . \
    && cd / \
    && rm -rf /tmp/dups

COPY bin/dups /usr/local/bin/dups
COPY entrypoint.sh /

RUN mkdir -p /backups

VOLUME ["/backups"]

ENTRYPOINT ["/entrypoint.sh"]


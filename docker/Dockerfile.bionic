FROM ubuntu:bionic

RUN apt-get update

# prep dependencies
RUN apt-get install -y --no-install-recommends \
    openssh-server python3

RUN mkdir /var/run/sshd

# dups system dependencies
RUN apt-get install --no-install-recommends -y \
    openssh-client rsync dbus libnotify-dev python3-gi libdbus-1-dev

# dups python requirements
RUN apt-get install --no-install-recommends -y \
    python3-dbus python3-paramiko python3-ruamel.yaml

COPY tests/.ssh /root/.ssh
RUN chmod -R 700 /root/.ssh

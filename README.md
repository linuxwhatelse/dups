dups
====
[![Say Thanks!](https://img.shields.io/badge/say-thanks-e91e63.svg)](https://saythanks.io/to/tadly)
[![Build Status](https://travis-ci.org/linuxwhatelse/dups.svg?branch=master)](https://travis-ci.org/linuxwhatelse/dups)

**Even though I actively use `dups` already, it should still be considered alpha!**

_It deduplicates things - Backup as simple as possible._

As there was no linux backup solution that was simple and
_to the point_-enough to fit my needs, I decided to write my own.

`dups` is powered by `rsync` using the amazing `--link-dest` option to
save space **and** time when backing up.

What this does is it creates [hard links](https://en.wikipedia.org/wiki/Hard_link)
to **unchanged** files from the previous backup meaning they don't have to be
transfered again **and** do not take up additional disk space.

Another priority of mine was the ability to acces backups without any special
software.
As each backup is just a _dumb_ replication of your local content, this is
easily achieved.


## Table of Contents
* [Todo](#todo)
* [Requirements](#requirements)
  * [System dependencies](#system-dependencies)
  * [Python dependencies](#python-dependencies)
* [Installation](#installation)
  * [archlinux](#archlinux)
  * [Other](#other)
* [Configuration](#configuration)
* [Usage](#usage)
  * [Including / Excluding items](#including-/-excluding-items)
  * [Listing includes / excludes](#listing-includes-/-excludes)
  * [Remove includes / excludes](#remove-includes-/-excludes)
  * [Start a backup](#start-a-backup)
  * [Delete a backup](#delete-a-backup)
  * [Start a restore](#start-a-restore)
  * [In the background](#in-the-background)
* [Gotchas / FAQ](#gotchas-faq)

## Todo
A **Logo / App icon** is still very much needed.  
If you feel like helping out, [here](https://github.com/linuxwhatelse/dups/issues/4)
is where you can ask questions, post designs etc.  
To anyone helping out, thank you very very much! I do really appreciate it!


## Requirements
### System dependencies
```
# Package-names may varry on your system

# Based on Archlinux
rsync
dbus
python-gobject
python-dbus
python-paramiko
python-ruamel-yaml

# Based on Ubuntu bionic
rsync
dbus
python3-gi
libdbus-1-dev
python3-dbus
python3-paramiko
python3-ruamel.yaml
```

### Python dependencies
```
# Runtime
dbus-python
paramiko
ruamel.yaml>=0.15.0

# Unittests
ddt
```


## Installation
### archlinux
There's a package in the aur: [python-dups-git](https://aur.archlinux.org/packages/python-dups-git/)

### Other
```sh
$ git clone https://github.com/linuxwhatelse/dups && cd dups
$ pip install .
$ cp data/systemd/dups.service ~/.config/systemd/user/
```


## Configuration
`dups` reads its config from `~/.config/dups/config.yaml` (create it if it
doesn't exist) and combines it with default values which you
can find [here](dups/data/config.yaml).

Hence a basic user config would look something like this:
```yaml
target:
  path: '/absolute/path/to/remote/backup/directory'
  host: 'backup-server-hostname'
  username: 'root'
```
`dups` can read your `ssh_config` so you may only specify a `path` and `host`.


## Usage
`dups`'s help text is your friend :)
```sh
dups --help
```

### Including / Excluding items
To add files, folders or patterns to the list of includes/excludes you can:
```sh
# Include some directories
$ dups --include ~/.config ~/.local/share

# Include some files
$ dups --include ~/.gitconfig ~/.bash_profile

# Include all files/folders ending with "rc" (e.g. .vimrc, .bashrc)
$ dups --include "$HOME/*rc"

# Exclude some directories
$ dups --exclude ~/.local/share/Trash ~/.local/share/tracker

# Exclude based on a pattern (note the quotes)
$ dups --exclude '*.zip' '*.iso' '*mp3' '*.txt'
```

### Listing includes / excludes
```sh
# List all included items
$ dups --list-includes

# List all excluded items
$ dups --list-excludes
```

### Remove includes / excludes
```sh
# Remove a file from the include list
$ dups --remove-includes ~/.bash_profile

# Remove a pattern from the exclude list
$ dups --remove-excludes '*.txt'
```

### Start a backup
```sh
$ dups --backup
```


### Delete a backup
```sh
# Remove a specific backup
$ dups --remove <backup name>

# Remove all old backups but keep 14 generations
$ dups --remove-but-keep 14

# Remove all backups older than 14 days
# See dups --help for possible values
$ dups --remove-older-than 14d
```

### Start a restore
```sh
# Restore the entire most recent backup to its original location
$ dups --restore

# Restore a file from a specific backup to a specific location
$ dups --restore <backup-name> --items $HOME/.vimrc --target /tmp/
```

### In the background
Backup and restore tasks can be run in the background if a daemon instance is
running.

A daemon can be started manually (this call is blocking)...
```sh
$ dups --daemon
```

...or via the included [systemd service](/data/systemd/dups.service).
```sh
$ systemctl --user start dups.service
```
If this service is not available to you (most likely because it hasn't been
packaged for your distribution) you can simply copy it to
`~/.config/systemd/user/dups.service`.

After reloading the user-units, you should be able to start it:
```sh
$ systemctl --user daemon-reload
$ systemctl --user start dups.service
```

Now you can instruct the daemon to run your backup:
```sh
$ dups --backup --background
```


## Gotchas / FAQ
### User/Group for files and folders are not properly backed up.
On unix systems it is typical that **only** root is able to change a
folders/files user and group.  
To keep the user and group, you'd have to connect with **root** to the remote
system.  

On my server I use [this docker image](https://hub.docker.com/r/kyleondy/rsync/)
to receive backups.

### How do I automate backups?
Currently using cron.  
I suggest using `anacron` (Ubuntu, Debian...) or `cronie` (archlinux) so if
your PC was turned off or suspended, tasks will still be run afterwards.

A cron entry could look something like:
```sh
# This starts a backup at 20:00 and does:
#   1. Wait up to 5 minutes for a valid network connection
#   2. Remove all but keep 13 backups
#   3. Start a new backup in the background
0 20 * * * nm-online -q -t 300; dups --remove-but-keep 13; dups --background --backup
```

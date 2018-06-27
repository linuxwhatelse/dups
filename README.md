dups
====
[![Build Status](https://travis-ci.org/linuxwhatelse/dups.svg?branch=master)](https://travis-ci.org/linuxwhatelse/dups)

**Even though I actively use `dups` already, it should still be considered alpha!**

It deduplicates things - Backup as simple as possible.

As there was no linux backup solution that was simple and
_to the point_-enough to fit my needs, I decided to write my own.

`dups` is powered by `rsync` using the amazing `--link-dest` option to
save space **and** time when backing up.

What this does is it creates [hard links](https://en.wikipedia.org/wiki/Hard_link) to **unchanged** files from the
previous backup meaning they don't have to be transfered again **and** do not
take up additional disk space.

Another priority of mine was the ability to acces backups without any special
software.
As each backup is just a _dumb_ replication of your local content, this is
easily achieved.


## Requirements
### System dependencies
```
rsync>=2.6.7
libnotify
```

### Python dependencies
```
dbus-python
paramiko
ruamel.yaml
```


## Todo
- [ ] Unit tests
- [ ] Remove old backups based on the [GFS](https://en.wikipedia.org/wiki/Backup_rotation_scheme#Grandfather-father-son) rotation scheme
- [ ] Logo/App icon preferably fitting the [Paper Icon Theme](https://snwh.org/paper) (help wanted)


## Installation
### archlinux
There's a package in the aur: [dups-git](https://aur.archlinux.org/packages/dups-git/)

### Other
```sh
pip install git+https://github.com/linuxwhatelse/dups
```


## Configuration
`dups` reads its config from `~/.config/dups.yaml` (create it if it doesn't
exist) and combines it with some default values which you can find [here](dups/data/config.yaml).

Hence a basic user config would look something like this:
```yaml
target:
  path: '/absolute/path/to/remote/backup/directory'
  host: 'backup-server-hostname'
  username: 'root'
```


## Gotchas
### User/Group for files and folders are not properly backed up.
On unix systems it is typical that **only** root can change a files/folders
user and group.
To keep the user and group, you'd have to connect with root to the remote system.


## Usage
For the time being, here's the help text.
```text
usage: dups [-h] [-B] [-R [NAME]] [--items ITEMS [ITEMS ...]]
            [--target TARGET] [-r REMOVE [REMOVE ...]]
            [--remove-but-keep [REMOVE_BUT_KEEP]]
            [--remove-older-than [REMOVE_OLDER_THAN]] [-l]
            [-i INCLUDE [INCLUDE ...]] [-li]
            [-ri REMOVE_INCLUDES [REMOVE_INCLUDES ...]]
            [-e EXCLUDE [EXCLUDE ...]] [-le]
            [-re REMOVE_EXCLUDES [REMOVE_EXCLUDES ...]] [--daemon] [-bg]
            [--dry-run]

It deduplicates things - Backup as simple as possible.

optional arguments:
  -h, --help            show this help message and exit

Backup:
  -B, --backup          Start a new backup.

Restore:
  -R [NAME], --restore [NAME]
                        Start a new restore. If name is omitted or set to
                        "latest", the most recent backup is used. Use
                        "-l|--list" to get a list of available backups.
  --items ITEMS [ITEMS ...]
                        Restore the given files/folders. If omitted, the
                        entire backup will be restored.
  --target TARGET       Where to restore to. If omitted or set to "/", all
                        files will be restored to their original location.

Remove:
  -r REMOVE [REMOVE ...], --remove REMOVE [REMOVE ...]
                        Remove the given backups. This can NOT be undone! Use
                        "-l|--list" to get a list of available backups.
  --remove-but-keep [REMOVE_BUT_KEEP]
                        Remove all but keep this many of most recent backups.
                        This can NOT be undone!
  --remove-older-than [REMOVE_OLDER_THAN]
                        Remove all backups older than this where "this"
                        referes to a combination of a "number" and a
                        "identifier". The identifier can be one of "s"
                        Seconds, "m" Minutes, "h" Hours, "d" Days or "w"
                        Weeks. e.g "1w" would refer to "1 week". This can NOT
                        be undone!

Management:
  -l, --list            List all available backups.
  -i INCLUDE [INCLUDE ...], --include INCLUDE [INCLUDE ...]
                        Add folders, file and/or patterns to the include list.
                        When adding patterns, surround them with quotes to
                        ensure they are not resolved to files or folders.
  -li, --list-includes  List all folders, files and pattern from the include
                        list.
  -ri REMOVE_INCLUDES [REMOVE_INCLUDES ...], --remove-includes REMOVE_INCLUDES [REMOVE_INCLUDES ...]
                        Remove the given items from the include list.
  -e EXCLUDE [EXCLUDE ...], --exclude EXCLUDE [EXCLUDE ...]
                        Add folders, file and/or patterns to the exlude list.
                        When adding patterns, surround them with quotes to
                        ensure they are not resolved to files or folders.
  -le, --list-excludes  List all folders, files and pattern from the exclude
                        list.
  -re REMOVE_EXCLUDES [REMOVE_EXCLUDES ...], --remove-excludes REMOVE_EXCLUDES [REMOVE_EXCLUDES ...]
                        Remove the given items from the exclude list.

Other:
  --daemon              Start a daemon.
  -bg, --background     Perform the given task in the background. A running
                        daemon is required. See "--daemon". Only applies to "
                        --backup" and "--restore".
  --dry-run             Perform a trial run with no changes made. Only applies
                        to "--backup", "--restore" and all "remove" functions.
```

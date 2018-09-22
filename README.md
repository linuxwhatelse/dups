# dups
[![Say Thanks!](https://img.shields.io/badge/say-thanks-e91e63.svg)](https://saythanks.io/to/tadly)
[![Build status](https://ci.appveyor.com/api/projects/status/ia8xtstfs2bkxu8g/branch/master?svg=true)](https://ci.appveyor.com/project/tadly/dups/branch/master)

dups is a simple backup utility which uses [rsync](https://rsync.samba.org/)
for the heavy lifting in the background and adds some sugar around it.  
  
To reduce disk space and subsequent backup times, dups relies on rsyncs
`--link-dest` option which hardlinks to existing unchanged files.


## Motivation
Beeing unable to find a backup utility which would allow me to...
  * backup selected files and folders
  * exclude files and folders based on their path or patterns
  * easily access stored files without special tools  
    (This includes the backup software itself)
  * doesn't come with to much bloat

...I ended up writing my own.  
This is not to say other software is bad, just not what I was
looking for.


## Getting Started
See [deployment](#deployment) for notes on how to deploy dups on a live system.

### Prerequisites
Required system packages:
```
rsync
```

Required python packages:
```
# Runtime
paramiko
ruamel.yaml>=0.15.0

# Runtime (Optional)
dbus-python  # Daemon support
pygobject  # Desktop notification support

# Unittests
ddt
```

### Installing
After all [prerequisites](#prerequisites) have been met, dups can be installed
with:
```sh
$ git clone https://github.com/linuxwhatelse/dups
$ cd dups
$ python setup.py install
```

System files for dbus, systemd etc. can be included by setting
`INCLUDE_DATA_FILES` prior to running the installation.  
This will require root access to copy the files to their respective location
and is therefore ill-advised for live systems.  
For live systems, see [deployment](#deployment) instead.
```sh
$ export INCLUDE_DATA_FILES="systemd dbus desktop"
$ python setup.py install
```
For possible values see `get_data_files` in [setup.py](setup.py).  
  
Build files/scripts for some distributions can be found in
[data/pkg/](data/pkg/).

### Usage
For a full setup guide and usage examples see the
[wiki](https://github.com/linuxwhatelse/dups/wiki).

As a quick overview, here's dups main help message.  
Individual commands may have additional arguments.
```
usage: dups [-h] [-u [USER]] [-c [CONFIG]] <command> ...

It deduplicates things - Backup as simple as possible.

optional arguments:
  -h, --help            show this help message and exit
  -u [USER], --user [USER]
                        Pretend to be this user for reading the config file,
                        writing logs etc. while preserving the original users
                        access rights. Only useful when run with elevated
                        privileges.
  -c [CONFIG], --config [CONFIG]
                        Use this config file instead.

Commands:
  <command>
    backup (b)          Start a new backup.
    list (l)            List backups.
    info (I)            Retrieve detailed backup info.
    modify (m)          Modify the given backup(s).
    restore (r)         Start a new restore.
    remove (rm)         Remove one or more backups.
    logs                Print the most recent log.
    include (i)         Add items to be included.
    list-includes (li)  List included items.
    remove-includes (rmi)
                        Remove included items.
    exclude (e)         Add items to be excluded.
    list-excludes (le)  List excluded items.
    remove-excludes (rme)
                        Remove excluded items.
    daemon (d)          Start a daemon instance.
```

## Deployment
Packages for some distributions are automatically built and are available in
the [release](https://github.com/linuxwhatelse/dups/releases) section.
  
Additionally, the following distributions have a version accessible through
their package-manager.

| Distribution | Link |
| --- | --- |
| archlinux | [aur - python-dups-git](https://aur.archlinux.org/packages/python-dups-git/) |


## Contributing
A contribution guide does not yet exists.  
  
Just ensure the code quality is up to par (or better) with the existing one
and unit-test don't fail.  
New features should also be properly unittested.


## Authors
* **tadly** - *Initial work* - [tadly](https://github.com/tadly)


## License
This project is licensed under the GNU General Public License v3.0 - see the
[LICENSE](LICENSE) file for details

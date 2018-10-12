<p align="center">
  <img alt="dups banner" width="300" src="https://github.com/linuxwhatelse/dups/blob/master/media/dups-banner.png">
</p>
<p align="center">
  <a href="https://saythanks.io/to/tadly">
    <img alt="Say Thanks" src="https://img.shields.io/badge/say-thanks-e91e63.svg">
  </a>
  <a href="https://ci.appveyor.com/project/tadly/dups/branch/master">
    <img alt="Build status" src="https://ci.appveyor.com/api/projects/status/ia8xtstfs2bkxu8g/branch/master?svg=true">
  </a>
</p>

# Overview
dups is a simple backup utility using [rsync](https://rsync.samba.org/) for
its heavy lifting while adding some convenience on top.  
  
To reduce disk space and subsequent backup times, dups relies on rsyncs
`--link-dest` option which hardlinks to existing unchanged files.


## Motivation
Being unable to find a backup utility which would allow me to...
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
[[ req-sys ]]
```

Required python packages:
```
[[ req-py ]]
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
[[ help ]]
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
Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.


## Authors
* **tadly** - *Initial work* - [tadly](https://github.com/tadly)


## Credits
* **Andela Denaro** - *Logo design* - [andeladenaro](https://github.com/andeladenaro)


## License
This project is licensed under the GNU General Public License v3.0 - see the
[LICENSE](LICENSE) file for details

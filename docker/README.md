# dups
A alpine linux based dups client for scheduled backups.


## Configuration
Key aspects of the container can be configured through the following
environment variables:

 * `BACKUP_SCHEDULE`  
    Cron style string at which to start a backup.  
    Defaults to: `0 0 * * *`
 * `BACKUP_COMMAND`  
    Command used to run a new backup.  
    Defaults to: `dups backup`
 * `PRUNE_SCHEDULE`  
    Cron style string at which to prune backups.  
    Defaults to: `0 1 * * *`
 * `PRUNE_COMMAND`  
    Command used to prune backups.  
    Defaults to: `dups rm -y --gffs`


## Setup
### 1. Create a default config file on the host
```sh
$ echo -e "target:\n  path: /backups" > <host-path>/config/dups.yaml
```


### 2. Create a container
#### docker-compose
```yaml
version: '3.7'

services:
  dups:
    container_name: dups
    image: tadly/dups
    environment:
      BACKUP_SCHEDULE: '0 23 * * *'
      PRUNE_SCHEDULE: '30 23 * * *'
    volumes:
      - '<host-path>/config:/config'
      - '<host-path>/backups:/backups'
      - '/:/data:ro'
    restart: unless-stopped
```

#### Manually
```sh
$ docker create \
    --name=dups \
    -e BACKUP_SCHEDULE='0 23 * * *' \
    -e PRUNE_SCHEDULE='30 23 * * *' \
    -v '<host-path>/config:/config' \
    -v '<host-path>/backups:/backups' \
    -v '/:/data:ro' \
    tadly/dups
```


## Using dups
Usage is just like outside a container. To get started check out
the [official wiki](https://github.com/linuxwhatelse/dups/wiki). 

To run dups you can either run it from the host:
```sh
# When adding items make sure the paths match the one **inside** your
# container and **NOT** the one on your host.
#   
# In the container creation examples above, the file
# `/home/<user>/important.txt` would actually be
# `/data/home/<user>/important.txt`
$ docker exec dups dups -h
```

or connect to the container and run it from there:
```sh
$ docker exec -it dups sh
$ dups -h
```

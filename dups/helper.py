import datetime
import os
from contextlib import contextmanager
from typing import Tuple

from . import backup, config, const, daemon, exceptions, rsync, utils

CFG = config.Config.get()


def get_configured_io():
    """Get a `io.IO`_ instance based on the users configuration.
       Better use `configured_io`_ to automatically close sessions.

    Returns:
        io.IO: A instance of `io.IO`_.
    """
    t = CFG.target
    return utils.IO.get(t['host'], t['port'], t['username'],
                        config_file=t['ssh_config_file'],
                        key_file=t['ssh_key_file'])


@contextmanager
def configured_io():
    """Contextmanager wrapper for `get_configured_io`_.

    Yields:
        io.IO: A instance of `io.IO`_.

    Example:
        >>> with configured_io() as io:
                pass
    """
    io = None
    try:
        io = get_configured_io()
        yield io

    finally:
        if io:
            io.close()


def notify(title, body=None, urgency=None, icon=const.APP_ICON):
    """Send a new notification to a notification daemon unless configured
       otherwise by the user.

    Args:
        title (str): The notifications title.
        body (str): The notifications body.
        urgency (utils.NUrgency): The notifications urgency level.
        icon (str): Name or path of the notifications icon.
    """
    if not CFG.notify:
        return

    utils.notify(title, body, urgency, icon, const.APP_NAME)


def get_backups(include_valid=True, include_invalid=True):
    """Get a sorted list of all available backups.

    Returns:
        list: A sorted list of `backup.Backup`_ for the users configured
            target.
    """
    with configured_io() as io:
        backups = sorted(
            backup.Backup.all_backups(io, CFG.target['path'], include_valid,
                                      include_invalid))
        return backups


def print_backups():
    """Print a list of all available backups in a pretty way."""
    backups = get_backups()

    print('Name', '\t\t', 'Date', '\t\t\t', 'Valid')
    for b in backups:
        valid = 'yes' if b.is_valid else 'no'
        print(b.name, '\t', b.name_pretty, '\t', valid)


def create_backup(dry_run=False,
                  background=False) -> Tuple[backup.Backup, rsync.Status]:
    """Creates a new backup based on the users configuration.

    Args:
        dry_run (bool): Whether or not to perform a trial run with no
            changes made.
        background (bool): Whether or not to instruct a daemon instance to
            perform the backup.

    Returns:
        tuple: (`backup.Backup`_, `rsync.Status`_) if `background`_ was set to
            `False`, (`None`, `None`) otherwise.
    """
    if background:
        client = daemon.Client.get()
        client.backup(dry_run)
        return None, None
    else:
        utils.add_logging_handler('backup.log')

        with configured_io() as io:
            bak = backup.Backup.new(io, CFG.target['path'])
            status = bak.backup(
                CFG.get_includes(True), CFG.get_excludes(True), dry_run)

            return bak, status


def restore_backup(items=None, name=None, target=None, dry_run=False,
                   background=False):
    """Starts a new restore based on the users configuration.

    Args:
        items (list): List of files and folders to be restored.
            If `None` or empty, the entire backup will be restored.
        name (str): The name of the backup to restore from.
            If `None`, the most recent backup will be used.
        target (str): Path to where to restore the backup to.
            If `None` or "/", all files will be restored to their original
            location.
        dry_run (bool): Whether or not to perform a trial run with no
            changes made.
        background (bool): Whether or not to instruct a daemon instance to
            perform the restore.

    """
    with configured_io() as io:
        if name:
            bak = backup.Backup.from_name(io, name, CFG.target['path'])
        else:
            bak = backup.Backup.latest(io, CFG.target['path'])

        if not bak:
            print('No backup to restore from!')
            return None, None

        if target:
            target = os.path.abspath(target)

        if background:
            name = bak.name
            client = daemon.Client.get()
            client.restore(items, name, target, dry_run)
            return None, None
        else:
            utils.add_logging_handler('restore.log')

            status = bak.restore(target, items, dry_run)
            return bak, status


def remove_backups(names, dry_run=False):
    """Remove the given backups based on the users configuration.

    Args:
        names (list): List of Names of backups to remove.
        dry_run (bool): Whether or not to perform a trial run with no
            changes made.
    """
    with configured_io() as io:
        for name in names:
            try:
                b = backup.Backup.from_name(io, name, CFG.target['path'])
            except exceptions.BackupNotFoundException:
                print('Backup "{}" does not exist!'.format(name))
                continue

            if not dry_run:
                b.remove()

            print('Successfully removed "{}"'.format(name))


def remove_but_keep(keep, dry_run=False):
    """Remove all but keep `keep` amount of the most recent backups.

    Args:
        keep (int): Amount of most recent backups to keep.
        dry_run (bool): Whether or not to perform a trial run with no
            changes made.
    """
    if keep == 0:
        names = list(b.name for b in get_backups())
    else:
        names = list(b.name for b in get_backups()[:-keep])

    remove_backups(names, dry_run)


def remove_older_than(duration, dry_run=False):
    """Remove all backups older than the given `duration`.

    Args:
        duration (str): Remove backups older than this.
            See `utils.duration_to_timedelta`_ for the format.
        dry_run (bool): Whether or not to perform a trial run with no
            changes made.
    """
    try:
        older_than = (
            datetime.datetime.now() - utils.duration_to_timedelta(duration))
    except ValueError:
        print('Invalid duration specified.')
        return

    names = list()
    for b in get_backups():
        if b.datetime > older_than:
            break
        names.append(b.name)

    remove_backups(names, dry_run)

import os
from typing import Tuple

from . import backup, config, daemon, exceptions, rsync, utils

CFG = config.Config.get()


def get_io():
    """Get a `io.IO`_ instance based on the users configuration.

    Returns:
        io.IO: A instance of `io.IO`_.
    """
    t = CFG.target
    return utils.IO.get(t['host'], t['port'], t['username'],
                        key_file=t['ssh_key_file'])


def notify(title, body='', icon='dialog-information'):
    """Send a new notification to a notification daemon unless configured
       otherwise by the user.

    Args:
        title (str): The notifications title.
        body (str): The notifications body.
        icon (str): Name or path of the notifications icon.
    """
    if not CFG.notify:
        return
    utils.notify(title, body, icon)


def get_backups():
    """Get a list of all available backups.

    Returns:
        list: A sorted list of `backup.Backup`_ for the users configured
            target.
    """
    io = get_io()
    return sorted(
        backup.Backup.all_backups(io, CFG.target['path'], True, True))


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
        io = get_io()
        bak = backup.Backup.new(io, CFG.target['path'])
        status = bak.backup(CFG.includes.keys(), CFG.excludes.keys(), dry_run)
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
    io = get_io()
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
        name = bak.label
        client = daemon.Client.get()
        client.restore(items, name, target, dry_run)
        return None, None
    else:
        status = bak.restore(target, items, dry_run)
        return bak, status


def remove_backups(names, dry_run=False, background=False):
    """Remove the given backups based on the users configuration.

    Args:
        names (list): List of Names of backups to remove.
        dry_run (bool): Whether or not to perform a trial run with no
            changes made.
        background (bool): Whether or not to instruct a daemon instance to
            perform the restore.
    """
    io = get_io()
    for name in names:
        try:
            b = backup.Backup.from_name(io, name, CFG.target['path'])
        except exceptions.BackupNotFoundException:
            print('Backup "{}" does not exist!'.format(name))
            continue

        if not dry_run:
            b.remove()

        print('Successfully removed "{}"'.format(name))

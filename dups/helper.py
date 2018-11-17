import datetime
import logging
import os
import shlex
import socket
import sys
import traceback
from contextlib import contextmanager
from typing import Tuple

import paramiko
import ruamel.yaml

from . import backup, config, const, exceptions, rsync, user, utils

try:
    from dbus.exceptions import DBusException
except ImportError:

    class DBusException(Exception):
        pass


LOGGER = logging.getLogger(__name__)


def configure_logger():
    """Configure the logger based on the config file."""
    cfg = config.Config.get()
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    for name, level in cfg.logging.items():
        logging.getLogger(name).setLevel(level)


def prepare_env(usr):
    os.environ['USER'] = usr.user
    os.environ['HOME'] = usr.home
    os.environ['XDG_RUNTIME_DIR'] = usr.xdg_runtime_dir


def prepare_config(config_file=None, usr=None):
    try:
        if config_file:
            config_file = os.path.abspath(config_file)
        else:
            if usr is None:
                usr = user.User()
            config_file = usr.config_file

        cfg = config.Config.get()
        cfg.config_file = config_file

    except FileNotFoundError:
        LOGGER.error('The config file "{}" does not exist.'.format(
            cfg.config_file))
        return None

    except Exception:
        LOGGER.error(
            'Invalid config at "{}".\nCheck for any syntax errors.'.format(
                cfg.config_file))
        return None

    return cfg


def configure_rsync(usr):
    """Configure rsync based on the config file."""
    cfg = config.Config.get()
    sync = rsync.rsync.get()

    sync.rsync_bin = cfg.rsync['rsync_bin']
    sync.ssh_bin = '{} {} {}'.format(const.SSH_WRAPPER_SCRIPT, usr.user,
                                     cfg.rsync['ssh_bin'])

    sync.ssh_config_file = cfg.target['ssh_config_file']

    sync.acls = cfg.rsync['acls']
    sync.xattrs = cfg.rsync['xattrs']
    sync.prune_empty_dirs = cfg.rsync['prune_empty_dirs']
    sync.out_format = cfg.rsync['out_format']


def get_configured_io():
    """Get a `io.IO`_ instance based on the users configuration.
       Better use `configured_io`_ to automatically close sessions.

    Returns:
        io.IO: A instance of `io.IO`_.
    """
    cfg = config.Config.get()

    t = cfg.target
    return utils.IO.get(t['host'], t['ssh_config_file'])


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


def error_handler(callback, *args, **kwargs):
    """Handle the given callback and catch all exceptions if some should
       arise.

    Args:
        callback (function): The function to execute.
        *args: Arguments to pass to the callback.
        **kargs: Keyword-Arguments to pass to the callback.

    Returns:
        tuple: A 4-tuple consisting of:
            0 (...): The callbacks result or `None` on error.
            1 (str): User presentable error message on error otherwise `None`
            2 (Exception): The raised exception on error otherwise `None`.
            3 (str): Traceback information on error otherwise `None`.
    """
    error_msg = None
    exception = None
    tb = None

    try:
        res = callback(*args, **kwargs)
        return (res, None, None, None)

    except (exceptions.BackupAlreadyExistsException,
            exceptions.BackupNotFoundException,
            exceptions.InvalidUserException,
            paramiko.ssh_exception.NoValidConnectionsError,
            paramiko.ssh_exception.SSHException) as err:
        exception = err
        tb = traceback.format_exc()
        error_msg = str(err)

    except paramiko.ssh_exception.BadHostKeyException as err:
        exception = err
        tb = traceback.format_exc()
        error_msg = 'Host key verification failed.'

    except (KeyError, socket.gaierror) as err:
        exception = err
        tb = traceback.format_exc()
        error_msg = 'Could not connect to host.'

    except DBusException as err:
        exception = err
        tb = traceback.format_exc()
        error_msg = 'Unable to connect to daemon. Is one running?'

    except KeyboardInterrupt as err:
        exception = err
        tb = traceback.format_exc()
        error_msg = 'Process cancelled.'

    except Exception as err:
        exception = err
        tb = traceback.format_exc()
        error_msg = 'Something bad happened. Try increasing the log-level.'
        error_msg += '\n'
        error_msg += str(err)

    return (None, error_msg, exception, tb)


def notify(title, body=None, priority=None, icon=const.APP_ICON):
    """Send a new notification to a notification daemon unless configured
       otherwise by the user.

    Args:
        title (str): The notifications title.
        body (str): The notifications body.
        priority (utils.NPriority): The notifications priority level.
        icon (str): Name or path of the notifications icon.
    """
    cfg = config.Config.get()

    if not cfg.notify:
        return

    try:
        utils.notify(const.APP_ID, title, body, priority, icon)
    except RuntimeError as e:
        LOGGER.warning(str(e))


def print_log(usr, backup=False, restore=False):
    """Print the most recent log file if it exists.

    Args:
        usr (user.User): The user from which to read the logs.
        backup (bool): If the backup log should be printed.
        restore (bool): If the restore log should be printed.
    """
    files = []
    if backup:
        files.append(os.path.join(usr.cache_dir, 'backup.log'))

    if restore:
        files.append(os.path.join(usr.cache_dir, 'restore.log'))

    for f in files:
        if not os.path.exists(f):
            continue

        with open(f, 'r') as f:
            print(f.read())


def get_backups(io, include_valid=True, include_invalid=True):
    """Get a sorted list of all available backups.

    Returns:
        list: A sorted list of `backup.Backup`_ for the users configured
            target.
    """
    cfg = config.Config.get()

    backups = sorted(
        backup.Backup.all_backups(io, cfg.target['path'], include_valid,
                                  include_invalid))

    return backups


def print_backups(include_valid=True, include_invalid=True):
    """Print a list of all available backups in a pretty way."""
    with configured_io() as io:
        backups = get_backups(io, include_valid, include_invalid)

        print('Name', '\t\t', 'Date', '\t\t\t', 'Valid', '\t', 'Size')
        for b in backups:
            valid = 'yes' if b.is_valid else 'no'

            size = b.info.get('bytes', None)
            if size is None:
                size = b.calculate_size()
            size = utils.bytes2human(size)

            print(b.name, '\t', b.name_pretty, '\t', valid, '\t', size)


def print_backup_info(name=None):
    """Print the given backup in a pretty way.

    Args:
        name (str): The name of the backup to print info for.
            If `None`, the most recent backup will be used.
    """
    cfg = config.Config.get()

    with configured_io() as io:
        try:
            if name:
                bak = backup.Backup.from_name(io, name, cfg.target['path'])
            else:
                bak = backup.Backup.latest(io, cfg.target['path'])
        except exceptions.BackupNotFoundException:
            print('Backup "{}" does not exist!'.format(name))
            return

        yaml = ruamel.yaml.YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.dump(bak.info, sys.stdout)


def create_backup(usr, dry_run=False,
                  client=None) -> Tuple[backup.Backup, rsync.Status]:
    """Creates a new backup based on the users configuration.

    Args:
        dry_run (bool): Whether or not to perform a trial run with no
            changes made.
        background (bool): Whether or not to instruct a daemon instance to
            perform the backup.

    Returns:
        rsync.Status: The status of the backup or `None` if `client` was set.
    """

    if client:
        client.backup(dry_run)
        return None

    utils.add_logging_handler('backup.log', usr)
    cfg = config.Config.get()

    includes = []
    for type_, items in cfg.get_includes().items():
        if type_ in ['files', 'folders']:
            items = list(
                shlex.quote(e) if not os.path.exists(e) else e for e in items)

        includes.extend(items)

    status = None
    with configured_io() as io:
        bak = backup.Backup.new(io, cfg.target['path'])
        status = bak.backup(includes, cfg.get_excludes(True), dry_run)

    return status


def restore_backup(usr, items=None, name=None, target=None, dry_run=False,
                   client=None):
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
    if client:
        name = '' if name is None else name
        client.restore(items, name, target, dry_run)
        return None

    utils.add_logging_handler('restore.log', usr)
    cfg = config.Config.get()

    with configured_io() as io:
        if name:
            bak = backup.Backup.from_name(io, name, cfg.target['path'])
        else:
            bak = backup.Backup.latest(io, cfg.target['path'])

        if not bak:
            raise exceptions.BackupNotFoundException(
                'No backup to restore from!')

        if target:
            target = os.path.abspath(os.path.expanduser(target))

        if items:
            items = [os.path.abspath(os.path.expanduser(i)) for i in items]

        status = bak.restore(target, items, dry_run)

    return status


def validate_backups(names, is_valid):
    """Change the given backups valid state based on the users configuration.

    Args:z
        names (list): List of Names of backups to remove.
        is_valid (bool): If the given backups should be set valid or invalid.
    """
    cfg = config.Config.get()

    with configured_io() as io:
        for name in names:
            try:
                b = backup.Backup.from_name(io, name, cfg.target['path'])
            except exceptions.BackupNotFoundException:
                print('Backup "{}" does not exist!'.format(name))
                continue

            b.set_valid(is_valid)

            print('Successfully modified "{}"'.format(name))


def remove_backups(names, dry_run=False):
    """Remove the given backups based on the users configuration.

    Args:
        names (list): List of Names of backups to remove.
        dry_run (bool): Whether or not to perform a trial run with no
            changes made.
    """
    cfg = config.Config.get()

    with configured_io() as io:
        for name in names:
            try:
                b = backup.Backup.from_name(io, name, cfg.target['path'])
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
    with configured_io() as io:
        if keep == 0:
            names = list(b.name for b in get_backups(io))
        else:
            names = list(b.name for b in get_backups(io)[:-keep])

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

    with configured_io() as io:
        names = list(
            b.name for b in get_backups(io) if b.datetime <= older_than)

    remove_backups(names, dry_run)


def remove_invalid(dry_run=False):
    """Remove all invalid backups.

    Args:
        dry_run (bool): Whether or not to perform a trial run with no
            changes made.
    """
    with configured_io() as io:
        names = list(b.name for b in get_backups(io, False))

    remove_backups(names, dry_run)


def remove_gffs(days, weeks, months, years, dry_run=False):
    """Remove backups based on the grandfather-father-son rotation scheme.

    Args:
        days (int): Amount of days per week to keep.
        weeks (int): Amount of weeks per month to keep.
        months (int): Amount of months per year to keep.
        years (int): Amount of years to keep.
        dry_run (bool): Whether or not to perform a trial run with no
            changes made.
    """
    cfg = config.Config.get()

    with configured_io() as io:
        backup_dates = list(b.datetime for b in get_backups(io))

        keep_dates = utils.rotate_gffs(
            backup_dates, days, weeks, months, years,
            weekday_full=cfg['gffs_weekday_full'])[4]

        remove_dates = [dt for dt in backup_dates if dt not in keep_dates]
        remove_names = list(
            dt.strftime(backup.Backup.NAME_FORMAT) for dt in remove_dates)

        remove_backups(remove_names, dry_run)

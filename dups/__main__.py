import argparse
import getpass
import logging
import sys

import dbus

from . import const, daemon, helper, user, utils

LOGGER = logging.getLogger(__name__)


def parse_args():
    """Parse all commandline arguments.

    Returns:
        argparse.Namespace: The parsed commandline arguments.
    """
    parser = argparse.ArgumentParser(
        const.APP_NAME,
        description='It deduplicates things - Backup as simple as possible.')

    global_group = parser.add_argument_group('Global')
    inc_ex_group = parser.add_argument_group('Include/Exclude')
    daemon_group = parser.add_argument_group('Daemon')

    subparsers = parser.add_subparsers(dest='command')

    backup_parser = subparsers.add_parser('backup', aliases=['b'],
                                          help='Start a new backup.')
    restore_parser = subparsers.add_parser('restore', aliases=['r'],
                                           help='Start a new restore.')
    remove_parser = subparsers.add_parser('remove', aliases=['rm'],
                                          help='Remove one or more backups.')

    backup_parser.add_argument('-l', '--list', action='store_true',
                               help='List all available backups.')

    restore_parser.add_argument(
        '-b', '--backup', metavar='BACKUP', dest='restore', type=str,
        default='latest', help='Name of the backup to restore from.'
        'If omitted or set to "latest", the most recent backup is used.')
    restore_parser.add_argument(
        'target', nargs='?', type=str, default=const.DEFAULT_RESTORE_PATH,
        help='Where to restore to. If omitted or set to "/", '
        'all files will be restored to their original location.')
    restore_parser.add_argument(
        'items', nargs='*', type=str,
        help='Restore the given files/folders. If omitted, the entire backup '
        'will be restored.')

    remove_parser.add_argument('remove', metavar='backup', nargs='*', type=str,
                               help='Remove the given backup(s).')
    remove_parser.add_argument(
        '--all-but-keep', nargs='?', type=int,
        help='Remove all but keep this many of most recent backups.')
    remove_parser.add_argument(
        '--older-than', nargs='?', type=str,
        help='Remove all backups older than this where "this" referes to a '
        'combination of a "amount" and a "identifier". The identifier '
        'can be one of "s" Seconds, "m" Minutes, "h" Hours, "d" Days or '
        '"w" Weeks. e.g "1w" would refer to "1 week".')

    for sp in [backup_parser, restore_parser, remove_parser]:
        if sp != remove_parser:
            sp.add_argument(
                '--bg', '--background', dest='background', action='store_true',
                default=False,
                help='Perform the given task on the session daemon.')

            sp.add_argument(
                '--sbg', '--system-background', dest='system_background',
                action='store_true', default=False,
                help='Perform the given task on the system daemon.')

        sp.add_argument('--dry-run', action='store_true', default=False,
                        help='Perform a trial run with no changes made.')

    global_group.add_argument(
        '-u', '--user', nargs='?', type=str, default=getpass.getuser(),
        help='Use this users configuration. Only usefull when running as '
        'root.')
    global_group.add_argument('-c', '--config', nargs='?', type=str,
                              help='Use this config file instead.')
    global_group.add_argument('-y', '--yes', action='store_true',
                              default=False,
                              help='Do not ask for confirmation.')

    inc_ex_group.add_argument(
        '-i', '--include', nargs='+', type=str,
        help='Add folders, file and/or patterns to the include list. '
        'When adding patterns use single quotes to ensure they '
        'are not resolved by your shell.')
    inc_ex_group.add_argument(
        '--li', '--list-includes', dest='list_includes', action='store_true',
        help='List all folders, files and pattern from the include list.')
    inc_ex_group.add_argument(
        '--ri', '--remove-includes', dest='remove_includes', nargs='+',
        type=str, help='Remove the given items from the include list.'
        'When removing patterns use single quotes to ensure they '
        'are not resolved by your shell.')

    inc_ex_group.add_argument(
        '-e', '--exclude', nargs='+', type=str,
        help='Add folders, file and/or patterns to the exlude list. '
        'When adding patterns use single quotes to ensure they '
        'are not resolved by your shell.')
    inc_ex_group.add_argument(
        '--le', '--list-excludes', dest='list_excludes', action='store_true',
        help='List all folders, files and pattern from the exclude list.')
    inc_ex_group.add_argument(
        '--re', '--remove-excludes', dest='remove_excludes', nargs='+',
        type=str, help='Remove the given items from the exclude list.'
        'When removing patterns use single quotes to ensure they '
        'are not resolved by your shell.')

    daemon_group.add_argument(
        '--daemon', action='store_true',
        help='Start a user session daemon. To properly backup/restore files '
        'owned by root, you need a system daemon.')
    daemon_group.add_argument(
        '--system-daemon', action='store_true',
        help='Start a system daemon. If desktop notifications are wanted, '
        'a session daemon is also required.')

    return parser.parse_args()


def handle(callback, *args, **kwargs):
    """Handle the given callback, print any errors and exit if necessary.

    Args:
        callback (function): The function to execute.
        *args: Arguments to pass to the callback.
        **kargs: Keyword-Arguments to pass to the callback.
    """
    success, res = helper.error_handler(callback, *args, **kwargs)

    if not success:
        print(res)
        sys.exit(1)

    return res


def handle_backup(args, usr):
    """Handle the backup sub-command.

    Args:
        args: (argparse.Namespace): The parsed commandline arguments.
        usr: (user.User): The user for which to perform this action.
    """
    if args.list:
        handle(helper.print_backups)
        return

    dbus_client = None
    if args.background or args.system_background:
        dbus_client = daemon.Client(getpass.getuser(), args.system_background)

    bak, status = handle(helper.create_backup, usr, args.dry_run, dbus_client)

    if status:
        print(status.message)
        sys.exit(status.exit_code)


def handle_restore(args, usr):
    """Handle the restore sub-command.

    Args:
        args: (argparse.Namespace): The parsed commandline arguments.
        usr: (user.User): The user for which to perform this action.
    """
    dbus_client = None
    if args.background or args.system_background:
        dbus_client = daemon.Client(getpass.getuser(), args.system_background)

    msg = 'Restore backup? This will overwrite all existing files!'
    if not args.yes and not utils.confirm(msg):
        return

    name = args.restore
    if args.restore == 'latest':
        name = None

    bak, status = handle(helper.restore_backup, usr, args.items, name,
                         args.target, args.dry_run, dbus_client)
    if status:
        print(status.message)
        sys.exit(status.exit_code)


def handle_remove(args):
    """Handle the remove sub-command.

    Args:
        args: (argparse.Namespace): The parsed commandline arguments.
    """
    if args.remove or args.all_but_keep or args.older_than:
        msg = 'Remove backup(s)? This can NOT be undone!'
        if not args.yes and not utils.confirm(msg):
            return

    if args.remove:
        handle(helper.remove_backups, args.remove, args.dry_run)

    elif args.all_but_keep is not None:
        handle(helper.remove_but_keep, args.all_but_keep, args.dry_run)

    elif args.older_than:
        handle(helper.remove_older_than, args.older_than, args.dry_run)


def handle_daemon(usr, system=False):
    """Handle starting a daemon

    Args:
        usr (user.User): User for which to start a daemon.
        system (bool): Whether or not a system (rather than a session) daemon
            should be started.

    Returns:
        int: A exit code.
    """
    try:
        daemon.Daemon.run(usr, system)

    except dbus.exceptions.DBusException:
        print('The system daemon requires root privileges.')
        return 1

    return 0


def handle_management(args, cfg):
    """Handle all arguments used to manage includes/excludes.

    Args:
        args: (argparse.Namespace): The parsed commandline arguments.
        cfg: (config.Config): The config to add/remove includes/exludes from.
    """
    if args.include:
        cfg.add_includes(args.include)

    if args.list_includes:
        print('\n'.join(sorted(cfg.get_includes(True))))

    if args.remove_includes:
        cfg.remove_includes(args.remove_includes)

    if args.exclude:
        cfg.add_excludes(args.exclude)

    if args.list_excludes:
        print('\n'.join(sorted(cfg.get_excludes(True))))

    if args.remove_excludes:
        cfg.remove_excludes(args.remove_excludes)


def main():
    """Entrypoint for dups."""
    args = parse_args()

    try:
        usr = user.User(args.user)
    except ValueError as e:
        print(e)
        sys.exit(1)

    helper.prepare_env(usr)

    cfg = helper.prepare_config(args.config, usr)
    if cfg is None:
        sys.exit(1)

    helper.configure_logger()
    helper.configure_rsync(usr)

    LOGGER.debug('Using config: %s', cfg.config_file)

    if args.command in ['backup', 'b']:
        handle_backup(args, usr)

    elif args.command in ['restore', 'r']:
        handle_restore(args, usr)

    elif args.command in ['remove', 'rm']:
        handle_remove(args)

    else:
        if args.daemon or args.system_daemon:
            code = handle_daemon(usr, args.system_daemon)
            sys.exit(code)

        else:
            handle_management(args, cfg)

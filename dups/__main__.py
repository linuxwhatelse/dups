import argparse
import getpass
import logging
import sys

from . import const, helper, user, utils

try:
    import dbus
    from . import daemon
except ImportError:
    dbus = None
    daemon = None

LOGGER = logging.getLogger(__name__)


def get_arg_parser():
    """Prepares all argument parsers.

    Returns:
        dict: Dict containing all argument parsers.
            `main` referse to the main argument parser.
            All other entries refer to subparsers.
    """
    parsers = {}
    parsers['main'] = argparse.ArgumentParser(
        const.APP_NAME,
        description='It deduplicates things - Backup as simple as possible.')

    parsers['main'].add_argument(
        '-u', '--user', nargs='?', type=str, default=getpass.getuser(),
        help='Pretend to be this user for reading the config file, writing '
        'logs etc. while preserving the original users access rights. '
        'Only useful when run with elevated privileges.')
    parsers['main'].add_argument('-c', '--config', nargs='?', type=str,
                                 help='Use this config file instead.')

    subparser = parsers['main'].add_subparsers(
        title='Commands', dest='command', metavar='<command>', required=True)

    # --- Create backups ---
    parsers['backup'] = subparser.add_parser('backup', aliases=['b'],
                                             help='Start a new backup.')

    # --- List backups ---
    parsers['list'] = subparser.add_parser('list', aliases=['l'],
                                           help='List backups.')

    parsers['list'].add_argument('-v', '--no-valid', action='store_true',
                                 help='List without valid backups.')
    parsers['list'].add_argument('-i', '--no-invalid', action='store_true',
                                 help='List without invalid backups.')

    # --- Backup info ---
    parsers['info'] = subparser.add_parser(
        'info', aliases=['I'], help='Retrieve detailed backup info.')

    parsers['info'].add_argument(
        'backup', type=str, nargs='?',
        help='Name of the backup to retrieve info for. If omitted, the most '
        'recent backup is used.')

    # --- Modify backups ---
    parsers['modify'] = subparser.add_parser(
        'modify', aliases=['m'], help='Modify the given backup(s).')

    parsers['modify'].add_argument('backup', nargs='*', type=str,
                                   help='Backup(s) to modify.')
    parsers['modify'].add_argument('--set-valid', action='store_true',
                                   help='Set the given backup(s) to be valid.')
    parsers['modify'].add_argument(
        '--set-invalid', action='store_true',
        help='Set the given backup(s) to be invalid.')

    # --- Restore backups ---
    parsers['restore'] = subparser.add_parser('restore', aliases=['r'],
                                              help='Start a new restore.')

    parsers['restore'].add_argument(
        '-b', '--backup', metavar='BACKUP', dest='restore', type=str,
        help='Name of the backup to restore from. If omitted, the most recent '
        'backup is used.')
    parsers['restore'].add_argument(
        '-n', '--nth', metavar='NTH', dest='restore_nth', nargs='?', type=int,
        help='Restore from the nth backup in reverse order. '
        '"0" would resolve to the most recent backup, "1" to the one before '
        'that and so on.')
    parsers['restore'].add_argument(
        'target', nargs='?', type=str, default=const.DEFAULT_RESTORE_PATH,
        help='Where to restore to. If omitted or set to "/", '
        'all files will be restored to their original location.')
    parsers['restore'].add_argument(
        'items', nargs='*', type=str,
        help='Restore the given files/folders. If omitted, the entire backup '
        'will be restored.')

    # --- Remove backups ---
    parsers['remove'] = subparser.add_parser(
        'remove', aliases=['rm'], help='Remove one or more backups.')

    parsers['remove'].add_argument('backup', nargs='*', type=str,
                                   help='Backup(s) to remove.')
    parsers['remove'].add_argument(
        '--all-but-keep', nargs='?', type=int,
        help='Remove all but keep this many of most recent backups.')
    parsers['remove'].add_argument(
        '--older-than', nargs='?', type=str,
        help='Remove all backups older than this where "this" referse to a '
        'combination of a "amount" and a "identifier". The identifier '
        'can be one of "s" Seconds, "m" Minutes, "h" Hours, "d" Days or '
        '"w" Weeks. e.g "1w" would refer to "1 week".')
    parsers['remove'].add_argument('--invalid', action='store_true',
                                   help='Remove all invalid backups.')

    # --- Print log ---
    parsers['log'] = subparser.add_parser('log',
                                          help='Print backup/restore logs.')
    parsers['log'].add_argument('-b', '--backup', action='store_true',
                                help='Print the most recent backup log.')
    parsers['log'].add_argument('-r', '--restore', action='store_true',
                                help='Print the most recent restore log.')

    # --- Backup common options ---
    for sp in [parsers['backup'], parsers['restore'], parsers['remove']]:
        if sp != parsers['remove']:
            sp.add_argument(
                '--bg', '--background', dest='background', action='store_true',
                help='Perform the given task on the session daemon.')

            sp.add_argument(
                '--sbg', '--system-background', dest='system_background',
                action='store_true',
                help='Perform the given task on the system daemon.')

            sp.add_argument('--log', action='store_true',
                            help='Print the most recent log.')

        if sp != parsers['backup']:
            sp.add_argument('-y', '--yes', action='store_true',
                            help='Do not ask for confirmation.')

        sp.add_argument('--dry-run', action='store_true',
                        help='Perform a trial run with no changes made.')

    # --- Include/Exclude commands ---
    parsers['include'] = subparser.add_parser(
        'include', aliases=['i'], help='List/Add/Remove include items.')
    parsers['i'] = parsers['include']
    parsers['include'].add_argument(
        'items', nargs='*', type=str,
        help='Folders, file and/or patterns to add/remove. Patterns only '
        'support the wildcard (*) character. '
        'When adding/removing patterns, use single quotes to ensure they are '
        'not resolved by your shell.')

    parsers['exclude'] = subparser.add_parser(
        'exclude', aliases=['e'], help='List/Add/Remove exclude items.')
    parsers['e'] = parsers['exclude']
    parsers['exclude'].add_argument(
        'items', nargs='*', type=str,
        help='Folders, file and/or patterns to be excluded. When adding '
        'patterns use single quotes to ensure they are not resolved by your '
        'shell.')

    # --- Include/Exclude common options ---
    for sp in [parsers['include'], parsers['exclude']]:
        sp.add_argument('-r', '--remove', action='store_true',
                        help='Instead of adding, remove the given item(s).')

        sp.add_argument('-l', '--list', action='store_true',
                        help='List all items.')
        sp.add_argument('-f', '--no-files', action='store_true',
                        help='List without files.')
        sp.add_argument('-F', '--no-folders', action='store_true',
                        help='List without folders.')
        sp.add_argument('-p', '--no-patterns', action='store_true',
                        help='List without patterns.')

    parsers['daemon'] = subparser.add_parser('daemon', aliases=['d'],
                                             help='Start a daemon instance.')
    parsers['daemon'].add_argument('--session', action='store_true',
                                   help='Start a user daemon.')
    parsers['daemon'].add_argument('--system', action='store_true',
                                   help='Start a system daemon.')

    return parsers


def handle(callback, *args, **kwargs):
    """Handle the given callback, print any errors and exit if necessary.

    Args:
        callback (function): The function to execute.
        *args: Arguments to pass to the callback.
        **kwargs: Keyword-Arguments to pass to the callback.
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
    dbus_client = None
    if args.background or args.system_background:
        dbus_client = daemon.Client(getpass.getuser(), args.system_background)

    bak, status = handle(helper.create_backup, usr, args.dry_run, dbus_client)

    if status:
        print(status.message)
        sys.exit(status.exit_code)


def handle_modify(args, usr):
    """Handle the modify sub-command.

    Args:
        args: (argparse.Namespace): The parsed commandline arguments.
        usr: (user.User): The user for which to perform this action.
    """
    if args.set_valid:
        handle(helper.validate_backups, args.backup, True)

    elif args.set_invalid:
        handle(helper.validate_backups, args.backup, False)


def handle_restore(args, usr):
    """Handle the restore sub-command.

    Args:
        args: (argparse.Namespace): The parsed commandline arguments.
        usr: (user.User): The user for which to perform this action.
    """
    dbus_client = None
    if args.background or args.system_background:
        dbus_client = daemon.Client(getpass.getuser(), args.system_background)

    name = args.restore

    if args.restore_nth:
        with helper.configured_io() as io:
            backups = sorted(
                helper.get_backups(io, include_invalid=False), reverse=True)

        if args.restore_nth > len(backups):
            print('You do not have {} backups yet.'.format(args.restore_nth))
            sys.exit(1)

        name = backups[args.restore_nth].name

    msg = 'Restore backup? This will overwrite all existing files!'
    if not args.yes and not utils.confirm(msg):
        sys.exit(1)

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
    if any((args.backup, args.all_but_keep, args.older_than, args.invalid)):
        msg = 'Remove backup(s)? This can NOT be undone!'
        if not args.yes and not utils.confirm(msg):
            return

    if args.backup:
        handle(helper.remove_backups, args.backup, args.dry_run)

    elif args.all_but_keep is not None:
        handle(helper.remove_but_keep, args.all_but_keep, args.dry_run)

    elif args.older_than:
        handle(helper.remove_older_than, args.older_than, args.dry_run)

    elif args.invalid:
        handle(helper.remove_invalid, args.dry_run)


def handle_daemon(usr, system=False):
    """Handle starting a daemon and exit if necessary.

    Args:
        usr (user.User): User for which to start a daemon.
        system (bool): Whether or not a system (rather than a session) daemon
            should be started.
    """
    try:
        daemon.Daemon.run(usr, system)

    except dbus.exceptions.DBusException:
        print('The system daemon requires root privileges.')
        sys.exit(1)


def handle_items(cfg, args):
    """Handle the include/exclude sub-command."""
    if args.command in ['include', 'i']:
        add = cfg.add_includes
        get = cfg.get_includes
        remove = cfg.remove_includes
    elif args.command in ['exclude', 'e']:
        add = cfg.add_excludes
        get = cfg.get_excludes
        remove = cfg.remove_excludes
    else:
        return

    if args.remove:
        remove(args.items)

    elif args.list:
        items = get()
        if args.no_files:
            del items['files']

        if args.no_folders:
            del items['folders']

        if args.no_patterns:
            del items['patterns']

        items = [item for elem in items.values() for item in elem]
        print('\n'.join(sorted(items)))

    else:
        add(args.items)


def is_dbus_required(args):
    """Check `dbus-python` is required.

    Args:
        args: (argparse.Namespace): The parsed commandline arguments.

    Returns:
        bool: `True` if the `dbus-python` is required, `False` otherwise.
    """
    if args.command in ['daemon', 'd']:
        return True

    if 'background' in args and args.background:
        return True

    if 'system_background' in args and args.system_background:
        return True

    return False


def main():  # noqa: C901
    """Entrypoint for dups."""
    parsers = get_arg_parser()
    args = parsers['main'].parse_args()

    if is_dbus_required(args) and dbus is None:
        print('To use any of the daemon functionality, "dbus-python" '
              'is required.')
        sys.exit(1)

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

    if args.command in ['list', 'l']:
        handle(helper.print_backups, not args.no_valid, not args.no_invalid)

    elif args.command in ['info', 'I']:
        handle(helper.print_backup_info, args.backup)

    elif args.command in ['backup', 'b']:
        handle_backup(args, usr)

    elif args.command in ['modify', 'm']:
        if not any((args.set_valid, args.set_invalid)):
            parsers['modify'].error('Missing at least one argument.')
        handle_modify(args, usr)

    elif args.command in ['restore', 'r']:
        handle_restore(args, usr)

    elif args.command in ['remove', 'rm']:
        handle_remove(args)

    elif args.command in ['log']:
        if not any((args.backup, args.restore)):
            parsers['log'].error('Missing at least one argument.')
        helper.print_log(usr, args.backup, args.restore)

    elif args.command in ['include', 'i', 'exclude', 'e']:
        if not any((args.items, args.list)):
            parsers[args.command].error('Missing items and/or arguments.')
        handle_items(cfg, args)

    elif args.command in ['daemon', 'd']:
        if not any((args.session, args.system)):
            parsers['daemon'].error('Missing at least one argument.')
        handle_daemon(usr, args.system)

import argparse
import getpass
import logging
import sys

import dbus

from . import const, daemon, helper

LOGGER = logging.getLogger(__name__)


def parse_args():
    """Parse all commandline arguments.

    Returns:
        argparse.Namespace: The parsed commandline arguments.
    """
    parser = argparse.ArgumentParser(
        const.APP_NAME,
        description='It deduplicates things - Backup as simple as possible.')

    backup_group = parser.add_argument_group('Backup')
    restore_group = parser.add_argument_group('Restore')
    remove_group = parser.add_argument_group('Remove')
    management_group = parser.add_argument_group('Management')
    daemon_group = parser.add_argument_group('Daemon')
    other_group = parser.add_argument_group('Other')

    backup_group.add_argument('-B', '--backup', action='store_true',
                              help='Start a new backup.')

    restore_group.add_argument(
        '-R', '--restore', metavar='NAME', dest='restore', nargs='?', type=str,
        const='latest',
        help='Start a new restore. If name is omitted or set to "latest", '
        'the most recent backup is used. '
        'Use "-l|--list" to get a list of available backups.')
    restore_group.add_argument(
        '--items', nargs='+', type=str,
        help='Restore the given files/folders. If omitted, the entire backup '
        'will be restored.')
    restore_group.add_argument(
        '--target', type=str, default=const.DEFAULT_RESTORE_PATH,
        help='Where to restore to. If omitted or set to "/", '
        'all files will be restored to their original location.')

    remove_group.add_argument(
        '-r', '--remove', nargs='+', type=str,
        help='Remove the given backups. This can NOT be undone! '
        'Use "-l|--list" to get a list of available backups.')
    remove_group.add_argument(
        '--remove-but-keep', nargs='?', type=int,
        help='Remove all but keep this many of most recent backups. '
        'This can NOT be undone!')
    remove_group.add_argument(
        '--remove-older-than', nargs='?', type=str,
        help='Remove all backups older than this where "this" referes to a '
        'combination of a "number" and a "identifier". The identifier '
        'can be one of "s" Seconds, "m" Minutes, "h" Hours, "d" Days or '
        '"w" Weeks. e.g "1w" would refer to "1 week". '
        'This can NOT be undone!')

    management_group.add_argument('-l', '--list', action='store_true',
                                  help='List all available backups.')
    management_group.add_argument(
        '-i', '--include', nargs='+', type=str,
        help='Add folders, file and/or patterns to the include list. '
        'When adding patterns, surround them with quotes to ensure they '
        'are not resolved to files or folders.')
    management_group.add_argument(
        '-li', '--list-includes', action='store_true',
        help='List all folders, files and pattern from the include list.')
    management_group.add_argument(
        '-ri', '--remove-includes', nargs='+', type=str,
        help='Remove the given items from the include list.')

    management_group.add_argument(
        '-e', '--exclude', nargs='+', type=str,
        help='Add folders, file and/or patterns to the exlude list. '
        'When adding patterns, surround them with quotes to ensure they '
        'are not resolved to files or folders.')
    management_group.add_argument(
        '-le', '--list-excludes', action='store_true',
        help='List all folders, files and pattern from the exclude list.')
    management_group.add_argument(
        '-re', '--remove-excludes', nargs='+', type=str,
        help='Remove the given items from the exclude list.')

    daemon_group.add_argument(
        '--daemon', action='store_true',
        help='Start a user session daemon. To properly backup/restore files '
        'owned by root, you need a system daemon. See "--system-daemon"')
    daemon_group.add_argument(
        '--system-daemon', action='store_true',
        help='Start a system daemon. If desktop notifications are wanted, '
        'a session daemon is also required. See "--daemon".')

    daemon_group.add_argument(
        '-bg', '--background', action='store_true', default=False,
        help='Perform the given task on the session daemon. See "--daemon". '
        'Only applies to "--backup" and "--restore".')
    daemon_group.add_argument(
        '-sbg', '--system-background', action='store_true', default=False,
        help='Perform the given task on the system daemon. See'
        '"--system-daemon". Only applies to "--backup" and "--restore".')

    other_group.add_argument(
        '-u', '--user', nargs='?', type=str, default=getpass.getuser(),
        help='Use this users configuration. Only usefull when running as '
        'root.')
    other_group.add_argument('-c', '--config', nargs='?', type=str,
                             help='Use this config file instead.')
    other_group.add_argument(
        '--dry-run', action='store_true', default=False,
        help='Perform a trial run with no changes made. '
        'Only applies to "--backup", "--restore" and all "remove" functions.')

    return parser.parse_args()


def handle_daemon(username, system=False):
    try:
        daemon.Daemon.run(username, system)

    except dbus.exceptions.DBusException:
        print('The system daemon requires root privileges.')
        return 1

    return 0


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


def main():
    """Entrypoint for dups."""
    args = parse_args()

    helper.prepare_env(args.user)

    # Exits if necessary
    cfg = helper.prepare_config(args.config)
    if cfg is None:
        sys.exit(1)

    helper.configure_logger()
    helper.configure_rsync(args.user)

    LOGGER.debug('Using config: %s', cfg.config_file)

    if args.daemon or args.system_daemon:
        sys.exit(handle_daemon(args.user, args.system_daemon))

    dbus_client = None
    if args.background or args.system_background:
        dbus_client = daemon.Client(getpass.getuser(), args.system_background)

    if args.backup:
        bak, status = handle(helper.create_backup, args.dry_run, dbus_client)

        if status:
            print(status.message)
            sys.exit(status.exit_code)
        sys.exit(0)

    if args.restore:
        # TODO: Ask user for confirmation
        name = args.restore
        if args.restore == 'latest':
            name = None
        bak, status = handle(helper.restore_backup, args.items, name,
                             args.target, args.dry_run, dbus_client)
        if status:
            print(status.message)
            sys.exit(status.exit_code)
        sys.exit(0)

    if args.list:
        handle(helper.print_backups)
        sys.exit(0)

    if args.remove:
        handle(helper.remove_backups, args.remove, args.dry_run)
        sys.exit(0)

    if args.remove_but_keep is not None:
        handle(helper.remove_but_keep, args.remove_but_keep, args.dry_run)
        sys.exit(0)

    if args.remove_older_than:
        handle(helper.remove_older_than, args.remove_older_than, args.dry_run)
        sys.exit(0)

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

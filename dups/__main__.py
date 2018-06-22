import argparse
import logging
import sys

import dbus
import paramiko

from . import config, const, daemon, exceptions, helper, rsync


def configure_logger():
    """Configure the logger based on the config file."""
    cfg = config.Config.get()
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    for name, level in cfg.logging.items():
        logging.getLogger(name).setLevel(level)


def configure_rsync():
    """Configure rsync based on the config file."""
    cfg = config.Config.get()
    sync = rsync.rsync.get()

    sync.rsync_bin = cfg.rsync['rsync_bin']
    sync.ssh_bin = cfg.rsync['ssh_bin']

    sync.acls = cfg.rsync['acls']
    sync.xattrs = cfg.rsync['xattrs']
    sync.prune_empty_dirs = cfg.rsync['prune_empty_dirs']
    sync.out_format = cfg.rsync['out_format']


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

    other_group.add_argument('--daemon', action='store_true', default=False,
                             help='Start a daemon.')
    other_group.add_argument(
        '-bg', '--background', action='store_true', default=False,
        help='Perform the given task in the background. A running daemon is '
        'required. See "--daemon". '
        'Only applies to "--backup" and "--restore".')
    other_group.add_argument(
        '--dry-run', action='store_true', default=False,
        help='Perform a trial run with no changes made. '
        'Only applies to "--backup", "--restore" and all "remove" functions.')

    return parser.parse_args()


def handle(callback, *args, **kwargs):
    """Handle the given callback and catch all exceptions if some should
       arise.

    Args:
        callback (function): The function to execute.
        *args: Arguments to pass to the callback.
        **kargs: Keyword-Arguments to pass to the callback.
    """
    try:
        return callback(*args, **kwargs)

    except paramiko.ssh_exception.SSHException as e:
        print(e)

    except KeyError as e:
        print('Unable to connect to {}'.format(e))

    except dbus.exceptions.DBusException as e:
        print('Unable to connect to daemon. Is one running?')
        print(e)

    except exceptions.BackupNotFoundException as e:
        print(e)

    except Exception as e:
        print('Something unforeseen happend. Try increasing the log-level.')
        print(e)

    sys.exit(1)


def main():
    """Entrypoint for dups."""
    args = parse_args()
    cfg = config.Config.get()

    configure_logger()
    configure_rsync()

    if args.daemon:
        daemon.Daemon.run()
        sys.exit(0)

    if args.backup:
        bak, status = handle(helper.create_backup, args.dry_run,
                             args.background)

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
                             args.target, args.dry_run, args.background)
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
        includes = sorted(cfg.includes.keys())
        print('\n'.join(includes))

    if args.remove_includes:
        cfg.remove_includes(args.remove_includes)

    if args.exclude:
        cfg.add_excludes(args.exclude)

    if args.list_excludes:
        excludes = sorted(cfg.excludes.keys())
        print('\n'.join(excludes))

    if args.remove_excludes:
        cfg.remove_excludes(args.remove_excludes)

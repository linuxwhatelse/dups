import sys
import argparse
import logging

import paramiko

from . import helper
from . import config


logging.basicConfig(level=logging.INFO, format='%(message)s')


def configure_logger(cfg):
    for name, level in cfg.logging.items():
        logging.getLogger(name).setLevel(level)


def parse_args():
    parser = argparse.ArgumentParser()

    backup_group = parser.add_argument_group('Backup')
    restore_group = parser.add_argument_group('Restore')
    remove_group = parser.add_argument_group('Remove')
    management_group = parser.add_argument_group('Management')
    other_group = parser.add_argument_group('Other')

    backup_group.add_argument(
        '--backup', action='store_true', help='Start a new backup.')

    restore_group.add_argument(
        '--restore', action='store_true', default=False,
        help='Start a new restore.')
    restore_group.add_argument(
        '--data', nargs='+', type=str,
        help='Restore the given files/folders.')
    restore_group.add_argument(
        '--target', type=str,
        help='Where to restore to. If omitted or set to "/", '
             'everything will be restored to its original location.')
    restore_group.add_argument(
        '--name', type=str,
        help='The backup to restore from. Use "-l|--list" to get a list of '
             'available backups. If omitted, the latest backup will be used.')

    remove_group.add_argument(
        '--remove', nargs='+', type=str,
        help='Remove the given backups. This can NOT be undone! '
             'Use "-l|--list" to get a list of available backups.')

    management_group.add_argument(
        '-l', '--list', action='store_true',
        help='List all available backups.')
    management_group.add_argument(
        '-i', '--include', nargs='+', type=str,
        help='Add folders, file and/or patterns to the include list.')
    management_group.add_argument(
        '-li', '--list-includes', action='store_true',
        help='List all folders, files and pattern from the include list.')
    management_group.add_argument(
        '-ri', '--remove-includes', nargs='+', type=str,
        help='Remove the given items from the include list.')

    management_group.add_argument(
        '-e', '--exclude', nargs='+', type=str,
        help='Add folders, file and/or patterns to the exlude list.')
    management_group.add_argument(
        '-le', '--list-excludes', action='store_true',
        help='List all folders, files and pattern from the exclude list.')
    management_group.add_argument(
        '-re', '--remove-excludes', nargs='+', type=str,
        help='Remove the given items from the exclude list.')

    other_group.add_argument(
        '--dry-run', action='store_true', default=False,
        help='Perform a trial run with no changes made. Only applies to '
             '"--backup", "--restore" and "--remove"')

    return parser.parse_args()


def handle(callback, *args, **kwargs):
    try:
        return callback(*args, **kwargs)

    except paramiko.ssh_exception.SSHException as e:
        print(e)

    except KeyError as e:
        print('Unable to connect to {}'.format(e))

    except Exception:
        print('Something unforeseen happend. Try increasing the log-level.')
        raise

    sys.exit(1)


def main():
    args = parse_args()
    cfg = config.Config.get()

    configure_logger(cfg)

    if args.backup:
        bak, status = handle(helper.create_backup, args.dry_run)
        print(status.message)
        sys.exit(status.exit_code)

    if args.restore:
        bak, status = handle(helper.restore_backup, args.data, args.name,
                             args.target, args.dry_run)
        if status:
            print(status.message)
            sys.exit(status.exit_code)
        sys.exit(0)

    if args.list:
        handle(helper.list_backups)
        sys.exit(0)

    if args.remove:
        handle(helper.remove_backups, args.remove, args.dry_run)
        sys.exit(0)

    if args.include:
        cfg.add_includes(args.include)

    if args.list_includes:
        includes = sorted(cfg.includes)
        print('\n'.join(includes))

    if args.remove_includes:
        cfg.remove_includes(args.remove_includes)

    if args.exclude:
        cfg.add_excludes(args.exclude)

    if args.list_excludes:
        excludes = sorted(cfg.excludes)
        print('\n'.join(excludes))

    if args.remove_excludes:
        cfg.remove_excludes(args.remove_excludes)

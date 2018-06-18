from . import backup
from . import config
from . import utils


CFG = config.Config.get()


def get_io():
    t = CFG.target
    return utils.IO.get(t['host'], t['port'], t['username'],
                        key_file=t['ssh_key_file'])


def get_backups():
    io = get_io()
    return sorted(backup.Backup.all_backups(
        io, CFG.target['path'], True, True))


def list_backups():
    backups = get_backups()
    print('Name', '\t\t', 'Date', '\t\t\t', 'Valid')
    for b in backups:
        valid = 'yes' if b.is_valid() else 'no'
        print(b.label, '\t', b.label_pretty, '\t', valid)


def create_backup(dry_run=False):
    io = get_io()
    bak = backup.Backup.new(io, CFG.target['path'])
    status = bak.backup(CFG.includes, CFG.excludes, dry_run)
    return bak, status


def restore_backup(includes, name=None, target='/', dry_run=False):
    io = get_io()
    if name:
        bak = backup.Backup.from_label(io, name, CFG.target['path'])
    else:
        bak = backup.Backup.latest(io, CFG.target['path'])

    if not bak:
        print('No backup found to restore from!')
        return None, None

    status = bak.restore(target, includes, dry_run)
    return bak, status


def remove_backups(names, dry_run=False):
    io = get_io()
    for name in names:
        try:
            b = backup.Backup.from_label(io, name, CFG.target['path'])
        except backup.BackupNotFoundException:
            print('Backup "{}" does not exist!'.format(name))
            continue
        if not dry_run:
            b.remove()
        print('Successfully removed "{}"'.format(name))

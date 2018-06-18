import os
import datetime
import logging

from . import utils
from . import rsync


LOGGER = logging.getLogger(__name__)


class BackupNotFoundException(Exception):
    pass


class BackupAlreadyExistsException(Exception):
    pass


class Backup:
    LABEL_FORMAT = '%Y%m%d%H%M%S'
    PRETTY_FORMAT = '%d, %b %Y %H:%M:%S'

    _label = None
    _backup_root_dir = None

    def __init__(self, io: utils.IO, root_dir, label):
        self._io = io
        self._backup_root_dir = root_dir
        self._label = label

    @classmethod
    def new(cls, io, root_dir):
        label = datetime.datetime.now().strftime(cls.LABEL_FORMAT)
        return cls(io, root_dir, label)

    @classmethod
    def from_label(cls, io, label, root_dir):
        backup = cls(io, root_dir, label)
        if not backup.exists():
            raise BackupNotFoundException
        return backup

    @classmethod
    def all_backups(cls, io, root_dir, include_valid=True,
                    include_invalid=False):
        backups = list()
        try:
            listing = io.listdir(root_dir)
        except FileNotFoundError:
            return list()

        for f in listing:
            try:
                datetime.datetime.strptime(f, cls.LABEL_FORMAT)
            except ValueError:
                continue

            bak = cls.from_label(io, f, root_dir)

            if include_valid and include_invalid:
                backups.append(bak)
                continue

            is_valid = bak.is_valid()
            if include_valid and is_valid:
                backups.append(bak)

            if include_invalid and not is_valid:
                backups.append(bak)

        return backups

    @classmethod
    def latest(cls, io, root_dir, include_valid=True, include_invalid=False):
        backups = sorted(cls.all_backups(io, root_dir, include_valid,
                                         include_invalid))
        if len(backups) == 0:
            return None
        return backups[0]

    def __str__(self):
        return self.label

    def __repr__(self):
        return self.label

    def __lt__(self, other):
        return self.label < other.label

    def __gt__(self, other):
        return self.label > other.label

    def __eq__(self, other):
        return self.label == other.label

    def __le__(self, other):
        return self.label <= other.label

    def __ge__(self, other):
        return self.label >= other.label

    def __ne__(self, other):
        return self.label != other.label

    @property
    def label(self):
        return self._label

    @property
    def label_pretty(self):
        dt = datetime.datetime.strptime(self.label, self.LABEL_FORMAT)
        return dt.strftime(self.PRETTY_FORMAT)

    @property
    def datetime(self):
        return datetime.datetime.strptime(self.label, self.LABEL_FORMAT)

    @property
    def backup_root_dir(self):
        return self._backup_root_dir

    @property
    def backup_dir(self):
        return os.path.join(self.backup_root_dir, self.label)

    @property
    def backup_data_dir(self):
        return os.path.join(self.backup_dir, 'data')

    @property
    def valid_path(self):
        return os.path.join(self.backup_dir, '.valid')

    @property
    def _previous_link(self):
        return os.path.join(self.backup_root_dir, '__previous')

    def exists(self):
        return self._io.exists(self.backup_dir)

    def is_valid(self):
        return self._io.exists(self.valid_path)

    def set_valid(self, valid):
        if valid:
            self._io.touch(self.valid_path)
        else:
            if self._io.exists(self.valid_path):
                self._io.remove(self.valid_path)

    def backup(self, includes, excludes=None, dry_run=False) -> rsync.Status:
        if self.exists():
            raise BackupAlreadyExistsException('This backup already exists!')

        sync = rsync.rsync.get()
        sync.dry_run = dry_run

        LOGGER.info('Creating backup directory: {}'.format(
            self.backup_data_dir))
        if not dry_run:
            self._io.makedirs(self.backup_data_dir)

        link_dest = None
        latest = self.latest(self._io, self.backup_root_dir, True, False)
        if latest:
            link_dest = latest.backup_data_dir

        target = rsync.Path(self.backup_data_dir, self._io.host,
                            self._io.port, self._io.username)
        sync = rsync.rsync.get()
        status = sync.send(target, includes, excludes, link_dest)

        if not dry_run and status.is_complete:
            self.set_valid(True)

        return status

    def restore(self, target, includes=None, dry_run=False) -> rsync.Status:
        if not self.exists():
            raise BackupNotFoundException('This backup does not exists!')

        sync = rsync.rsync.get()
        sync.dry_run = dry_run

        target = rsync.Path(target)

        sources = list()
        for include in includes:
            # Limit path information by insterting a dot and a slash into
            # the source path.
            # Documented in rsync under the `--relative` option
            include = os.path.join(self.backup_data_dir, '.',
                                   include.lstrip('/'))
            sources.append(rsync.Path(include, self._io.host, self._io.port,
                                      self._io.username))

        status = sync.receive(target, sources)

        return status

    def remove(self):
        if not self.exists():
            raise BackupNotFoundException('This backup does not exists!')

        self._io.rrmdir(self.backup_dir)

import datetime
import json
import logging
import os
from typing import List

from . import exceptions, rsync, utils

LOGGER = logging.getLogger(__name__)


class Backup(object):
    # Forward declaration for autocompletion to work with singletons
    pass


class Backup(object):
    """Class which represents a singular backup.

    Attributes:
        NAME_FORMAT (str): Formate used to generate the backups name.
            Do not change this value.
        PRETTY_FORMAT (str): Format used to generate a human readable
            representation of the backups name.
    """

    NAME_FORMAT = '%Y%m%d%H%M%S'
    PRETTY_FORMAT = '%a %d, %b %Y - %H:%M:%S'

    _name = None
    _backup_root_dir = None

    def __init__(self, io: utils.IO, root_dir, name):
        """Create a new instance of `Backup`_.
           Using `Backup.new`_ is the preferred method.

        Args:
            io (utils.IO): A IO instance with which to access the target.
            root_dir (str): Path to the root directory where backups are
                stored / will be stored.
            name (str): Name of the backup matching the format of
                `Backup.NAME_FORMAT`_.
        """
        self._io = io
        self._backup_root_dir = root_dir
        self._name = name

    @classmethod
    def new(cls, io: utils.IO, root_dir) -> Backup:
        """Create a new backup instance.

        Args:
            io (utils.IO): A IO instance with which to access the target.
            root_dir (str): Path to the root directory in which to
                store the backup.

        Returns:
            Backup: A instance of `Backup`_.
        """
        name = datetime.datetime.now().strftime(cls.NAME_FORMAT)
        return cls(io, root_dir, name)

    @classmethod
    def from_name(cls, io: utils.IO, name, root_dir) -> Backup:
        """Get an existing backup via its name.

        Args:
            io (utils.IO): A IO instance with which to access the target.
            name (str): A existing backups name matching the format of
                `Backup.NAME_FORMAT`_.
            root_dir (str): Path to the root directory in which backups
                are stored.

        Returns:
            Backup: A instance of `Backup`_.
        """
        backup = cls(io, root_dir, name)
        if not backup.exists:
            raise exceptions.BackupNotFoundException
        return backup

    @classmethod
    def all_backups(cls, io: utils.IO, root_dir, include_valid=True,
                    include_invalid=False) -> List[Backup]:
        """Get a list of all existing backups.

        Args:
            io (utils.IO): A IO instance with which to access the target.
            root_dir (str): Path to the root directory in which backups
                are stored.
            include_valid (bool): Whether or not to include valid backups.
            include_invalid (bool): Whether or not to include invalid backup.

        Returns:
            list: A list consisting of `Backup`_ instances.
        """

        backups = []
        try:
            listing = io.listdir(root_dir)
        except FileNotFoundError:
            return []

        for f in listing:
            try:
                datetime.datetime.strptime(f, cls.NAME_FORMAT)
            except ValueError:
                continue

            bak = cls.from_name(io, f, root_dir)

            if include_valid and include_invalid:
                backups.append(bak)
                continue

            is_valid = bak.is_valid
            if include_valid and is_valid:
                backups.append(bak)

            if include_invalid and not is_valid:
                backups.append(bak)

        return backups

    @classmethod
    def latest(cls, io: utils.IO, root_dir, include_valid=True,
               include_invalid=False) -> Backup:
        """Get the most recent backup.

        Args:
            io (utils.IO): A IO instance with which to access the target.
            root_dir (str): Path to the root directory in which backups
                are stored.
            include_valid (bool): Whether or not to include valid backups.
            include_invalid (bool): Whether or not to include invalid backups.

        Returns:
            Backup: A instance of `Backup`_.
        """
        backups = sorted(
            cls.all_backups(io, root_dir, include_valid, include_invalid),
            reverse=True)

        if len(backups) == 0:
            return None

        return backups[0]

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __lt__(self, other):
        if not isinstance(other, Backup):
            return False
        return self.name < other.name

    def __gt__(self, other):
        if not isinstance(other, Backup):
            return False
        return self.name > other.name

    def __eq__(self, other):
        if not isinstance(other, Backup):
            return False
        return self.name == other.name

    def __le__(self, other):
        if not isinstance(other, Backup):
            return False
        return self.name <= other.name

    def __ge__(self, other):
        if not isinstance(other, Backup):
            return False
        return self.name >= other.name

    def __ne__(self, other):
        if not isinstance(other, Backup):
            return False
        return self.name != other.name

    @property
    def name(self):
        """str: The backups name."""
        return self._name

    @property
    def name_pretty(self):
        """str: The backups name in a human readable fashion."""
        dt = datetime.datetime.strptime(self.name, self.NAME_FORMAT)
        return dt.strftime(self.PRETTY_FORMAT)

    @property
    def datetime(self):
        """datetime.datetime: When the backup was created."""
        return datetime.datetime.strptime(self.name, self.NAME_FORMAT)

    @property
    def backup_root_dir(self):
        """str: The root directory this backup will be/is stored in."""
        return self._backup_root_dir

    @property
    def backup_dir(self):
        """str: The directory this backup will be/is stored in."""
        return os.path.join(self.backup_root_dir, self.name)

    @property
    def backup_data_dir(self):
        """str: The directory this backups data will be/is stored in."""
        return os.path.join(self.backup_dir, 'data')

    @property
    def info_path(self):
        """str: Path to the backups '.info' file."""
        return os.path.join(self.backup_dir, '.info')

    @property
    def exists(self):
        """bool: Whether or not this backup exists."""
        return self._io.exists(self.backup_dir)

    @property
    def info(self):
        """dict: Data stored in the backups '.info' file."""
        if self._io.exists(self.info_path):
            with self._io.open(self.info_path, 'r') as f:
                try:
                    data = f.read()
                    if isinstance(data, bytes):
                        data = data.decode()
                    return json.loads(data)
                except Exception as e:
                    LOGGER.error(e)
        return {}

    @property
    def is_valid(self):
        """bool: Whether or not this is valid."""
        return self.info.get('valid', False)

    def set_info(self, key, value):
        """Set a info attribute for this backup.

        Args:
            key: The key to set/overwrite.
            value: The value to set.
        """
        info = self.info
        info[key] = value

        with self._io.open(self.info_path, 'w') as f:
            f.write(json.dumps(info, indent=2))

    def set_valid(self, valid):
        """Change the backups valid state.

        Args:
            valid (bool): `True` to set the backup valid, `False` otherwise.
        """
        self.set_info('valid', valid)

    def calculate_size(self):
        """Recalculate the size for this backup.

        Returns:
            int: The backups size in bytes.
        """
        size = 0
        if self._io.exists(self.backup_data_dir):
            size = self._io.calculate_size(self.backup_data_dir)

        self.set_info('bytes', size)

        return size

    def backup(self, items, excludes=None, dry_run=False) -> rsync.Status:
        """Create this backup if it doesn't already exist.

        Args:
            items (list): List of files, folders, and patterns to include
                in this backup.
            excludes (list): List of files, folders, and patterns to exclude
                from this backup.
            dry_run (bool): Whether or not to perform a trial run with no
                changes made.

        Returns:
            rsync.Status: The status of this backup.

        Raises:
            exceptions.BackupAlreadyExistsException: If the backup already
                exists.
        """
        if self.exists:
            raise exceptions.BackupAlreadyExistsException

        sync = rsync.rsync.get()
        sync.dry_run = dry_run

        LOGGER.info('Creating backup directory: {}'.format(
            self.backup_data_dir))
        if not dry_run:
            self._io.makedirs(self.backup_data_dir)
            self.set_info('backup_started_at',
                          datetime.datetime.now().strftime(self.PRETTY_FORMAT))

        link_dest = None
        latest = self.latest(self._io, self.backup_root_dir, True, False)
        if latest:
            link_dest = latest.backup_data_dir

        target = rsync.Path(self.backup_data_dir, self._io.host)
        status = sync.sync(target, items, excludes, link_dest)

        if not dry_run:
            self.set_info('backup_finished_at',
                          datetime.datetime.now().strftime(self.PRETTY_FORMAT))

            if self.info.get('size', None) is None:
                self.calculate_size()

            if status.exit_code == 0:
                self.set_valid(True)

        return status

    def restore(self, target, items=None, dry_run=False) -> rsync.Status:
        """Restore this backup.

        Args:
            target (str): Where to restore the data to.
            items (list): List of files and folders to be restored.
                If `None` or empty, the entire backup will be restored.
            dry_run (bool): Whether or not to perform a trial run with no
                changes made.

        Returns:
            rsync.Status: The status of the restore.

        Raises:
            exceptions.BackupNotFoundException: If the backup does not exists.
        """
        if not self.exists:
            raise exceptions.BackupNotFoundException

        if not items:
            items = [self.backup_data_dir]

        sync = rsync.rsync.get()
        sync.dry_run = dry_run

        target = rsync.Path(target)

        sources = []
        for item in items:
            # Limit path information by inserting a dot and a slash into
            # the source path.
            # Documented in rsync under the `--relative` option
            if item == self.backup_data_dir:
                item = os.path.join(self.backup_data_dir, '.', '')
            else:
                item = os.path.join(self.backup_data_dir, '.',
                                    item.lstrip('/'))

            sources.append(rsync.Path(item, self._io.host))

        status = sync.sync(target, sources)

        if not dry_run:
            restored_at = self.info.get('restored_at', [])
            restored_at.append(datetime.datetime.now().strftime(
                self.PRETTY_FORMAT))
            self.set_info('restored_at', restored_at)

        return status

    def remove(self):
        """Remove this backup.

        Raises:
            exceptions.BackupNotFoundException: If the backup does not exists.
        """
        if not self.exists:
            raise exceptions.BackupNotFoundException

        self._io.rrmdir(self.backup_dir)

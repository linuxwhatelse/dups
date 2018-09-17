import collections
import datetime
import errno
import functools
import logging
import logging.handlers
import os
import shutil
import stat
import subprocess
from contextlib import contextmanager
from copy import deepcopy

import paramiko

from . import config

try:
    from gi.repository import Gio
except ImportError:
    Gio = None


class NPriority:
    NORMAL, LOW, HIGH, URGENT = 0, 1, 2, 3


def confirm(msg, default_yes=False):
    """Let the user confirm a action with y (yes) or n (no).

    Args:
        msg (str): The message to display.
        default_yes (bool): If yes should be the default anwer when pressing
            return without supplying an answer.

    Returns:
        bool: `True` if confirmed, `False` otherwise.
    """
    msg = '{} {}: '.format(msg, '[Y/n]' if default_yes else '[y/N]')

    resp = ''
    while resp not in ['y', 'n']:
        try:
            resp = input(msg).lower()
            if not resp:
                resp = 'y' if default_yes else 'n'
        except KeyboardInterrupt:
            return False

    return resp == 'y'


def add_logging_handler(file_name, usr):
    """Add logging handler for all configured loggers.

    Args:
        file_name (str): The file name to write logs into.
    """
    cfg = config.Config.get()

    if not os.path.exists(usr.cache_dir):
        os.makedirs(usr.cache_dir)

    logfile = os.path.join(usr.cache_dir, file_name)
    do_rollover = os.path.exists(logfile)

    handler = logging.handlers.RotatingFileHandler(logfile, backupCount=7)

    if do_rollover:
        handler.doRollover()

    os.chown(usr.cache_dir, usr.uid, usr.gid)
    os.chown(logfile, usr.uid, usr.gid)

    for name, level in cfg.logging.items():
        logging.getLogger(name).addHandler(handler)


def notify(app_id, title, body=None, priority=None, icon=None):
    """Send a new notification to a notification daemon.

    Args:
        app_id (str): Unique id for the application posting this notification.
            Must follow the "D-Bus well-known bus names" scheme.
        title (str): The notifications title.
        body (str): The notifications body.
        priority (NPriority): The notifications priority level.
        icon (str): Name or path of the notifications icon.

    Raises:
        RuntimeError: If pygobject is missing.
    """
    if Gio is None:
        raise RuntimeError('"pygobject" required but not available.')

    app = Gio.Application.new(app_id, Gio.ApplicationFlags.FLAGS_NONE)
    app.register()

    notification = Gio.Notification.new(title)
    notification.set_body(body)

    if priority:
        notification.set_priority(priority)

    if icon:
        notification.set_icon(Gio.ThemedIcon.new(icon))

    app.send_notification(None, notification)


def dict_merge(defaults, new):
    """Recursively merge two dictionaries.

    Args:
        defaults (dict): Default values.
        new (dict): New values to merge into `defaults`.

    Returns:
        dict: Merged version of both dictionaries.
    """
    result = deepcopy(defaults)

    for key, val in new.items():
        if isinstance(val, collections.Mapping):
            result[key] = dict_merge(result.get(key, {}), val)
        elif isinstance(val, list):
            result[key] = result.get(key, []) + val
        else:
            result[key] = deepcopy(new[key])

    return result


def duration_to_timedelta(duration):
    """Converts a `duration` into a timedelta object based on the following
       scheme.

       =========   ======= ===================
       Character   Meaning Example
       =========   ======= ===================
       s           Seconds '60s' -> 60 Seconds
       m           Minutes '5m'  -> 5 Minutes
       h           Hours   '24h' -> 24 Hours
       d           Days    '7d'  -> 7 Days
       w           Weeks   '7w'  -> 7 Weeks
       =========   ======= ===================

    Returns:
        datetime.timedelta
    """
    num = int(duration[:-1])
    if duration.endswith('s'):
        return datetime.timedelta(seconds=num)

    elif duration.endswith('m'):
        return datetime.timedelta(minutes=num)

    elif duration.endswith('h'):
        return datetime.timedelta(hours=num)

    elif duration.endswith('d'):
        return datetime.timedelta(days=num)

    elif duration.endswith('w'):
        return datetime.timedelta(weeks=num)


def validate_absolute(func):
    """Decorator which checks if the first argument is a absolute path."""

    @functools.wraps(func)
    def wrapper(*args):
        for arg in args:
            if not isinstance(arg, str):
                continue

            if not os.path.isabs(arg):
                raise ValueError('Should be an absolute path!')

            break
        return func(*args)

    return wrapper


def bytes2human(n):
    """Convert the given bytes to a human readable representation.

    Args:
        n (int): bytes to convert.

    Returns:
        str: Human readable representation of the given bytes.
    """
    symbols = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')

    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i + 1) * 10

    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return '{:.2f} {}'.format(value, symbol)

    return '{:.2f} {}'.format(n, symbols[0])


class IO:
    # Forward declaration for autocompletion to work with singletons
    pass


class IO:
    """Class to abstract simple file operations for local and sftp."""
    __instances = {}

    _instance_key = None

    _ssh = None
    _sftp = None

    def __init__(self, host=None, config_file=None):
        """Create a new instance of `IO`_.
           Using `IO.get`_ is the preferred method.

        Args:
            See `IO.get`_ for a description of the arguments.
        """

        self._host = host
        self._config_file = config_file

        self._connect_remote()

    def __del__(self):
        if self._ssh:
            self._ssh.close()

        if self._instance_key in IO.__instances:
            del IO.__instances[self._instance_key]

    def close(self):
        self.__del__()

    @classmethod
    def get(cls, host=None, config_file=None) -> IO:
        """Get a instance of `IO`_ for the given arguments.

        Args:
            host (str): If remote, the host to connect to.
            config_file (str): If remote, the absolute path to the
                an ssh config file.

        Returns:
            IO: A existing (or new if it's the first call)
                instance of `IO`_ for the given arguments.
        """
        key = '{}_{}'.format(host, config_file)

        if key not in cls.__instances:
            cls.__instances[key] = cls(host, config_file)
            cls.__instances[key]._instance_key = key
        return cls.__instances[key]

    def _connect_remote(self):
        """Connect to the remote host."""
        if self.is_local:
            return

        self._ssh = paramiko.client.SSHClient()
        self._ssh.load_system_host_keys()
        self._ssh.set_missing_host_key_policy(paramiko.client.WarningPolicy())

        cfg = {
            'hostname': self.host,
            'port': 22,
            'user': None,
            'identityfile': os.path.expanduser('~/.ssh/id_rsa'),
        }

        if self.config_file and os.path.exists(self.config_file):
            ssh_config = paramiko.SSHConfig()
            with open(self.config_file) as f:
                ssh_config.parse(f)

            cfg = {**cfg, **ssh_config.lookup(self.host)}

        self._ssh.connect(cfg['hostname'], int(cfg['port']), cfg['user'],
                          look_for_keys=False,
                          key_filename=cfg['identityfile'])

        self._sftp = self._ssh.open_sftp()

    @property
    def host(self):
        """str: The host provided while creating this instance."""
        return self._host

    @property
    def config_file(self):
        """str: The key_file provided while creating this instance."""
        return self._config_file

    @property
    def is_local(self):
        """bool: Whether or not this is a local instance."""
        return self._host is None

    @validate_absolute
    def isfile(self, path):
        """Test if the given path is a file.

        Args:
            path (str): Absolute path of the file to test.

        Returns:
            bool: `True` if the given path is a file, `False` otherwise.

        Raises:
            ValueError: If the given path is not absolute.
            FileNotFoundError: If the given path does not exist.
        """
        if self.is_local:
            return os.path.isfile(path)

        try:
            return stat.S_ISREG(self._sftp.stat(path).st_mode)
        except FileNotFoundError:
            return False

    @validate_absolute
    def isdir(self, path):
        """Test if the given path is a directory.

        Args:
            path (str): Absolute path of the file to test.

        Returns:
            bool: `True` if the given path is a symbolic link, `False`
                otherwise.

        Raises:
            ValueError: If the given path is not absolute.
            FileNotFoundError: If the given path does not exist.
        """
        if self.is_local:
            return os.path.isdir(path)

        try:
            return stat.S_ISDIR(self._sftp.stat(path).st_mode)
        except FileNotFoundError:
            return False

    @validate_absolute
    def listdir(self, path):
        """List the contents of the given path.

        Args:
            path (str): Absolute path of the directory to list.

        Returns:
            list: All items found in the given directory.

        Raises:
            ValueError: If the given path is not absolute.
            FileNotFoundError: If the given path does not exist.
            AttributeError: If the given path is not a directory.
        """
        if self.is_local:
            return os.listdir(path)
        return self._sftp.listdir(path)

    @validate_absolute
    def mkdir(self, path):
        """Create a directory named `path`_.

        Args:
            path (str): Path which to create.

        Raises:
            ValueError: If the given path is not absolute.
        """
        if self.is_local:
            return os.mkdir(path)
        return self._sftp.mkdir(path)

    @validate_absolute
    def makedirs(self, path):
        """Recursively create directories.

        Args:
            path (str): Path which to create.

        Raises:
            ValueError: If the given path is not absolute.
        """
        if self.is_local:
            return os.makedirs(path, exist_ok=True)

        current = '/'
        # TODO: maybe use os.path.split
        for p in path.split('/'):
            current = os.path.join(current, p)
            if self.exists(current):
                continue
            self._sftp.mkdir(current)

    @validate_absolute
    def touch(self, path):
        """Creates an empty file named path.

        Args:
            path (str): File path to create.

        Raises:
            ValueError: If the given path is not absolute.
        """
        if self.is_local:
            return open(path, 'a').close()
        return self._sftp.open(path, 'a').close()

    @contextmanager
    @validate_absolute
    def open(self, path, mode='r'):
        """Open the given path for reading/writing.

        Yields:
            file: A file type object

        Example:
            >>> with IO.get().open('/tmp/test.file', 'w') as f:
                    f.write('Hello world!')
        """
        file_ = None
        try:
            if self.is_local:
                file_ = open(path, mode)
            else:
                file_ = self._sftp.file(path, mode)

            yield file_

        finally:
            if file_:
                file_.flush()
                file_.close()

    @validate_absolute
    def exists(self, path):
        """Test whether the given path exists.

        Args:
            path (str): Path which to test.

        Raises:
            ValueError: If the given path is not absolute.
        """
        if self.is_local:
            return os.path.exists(path)

        try:
            self._sftp.stat(path)
        except IOError as e:
            if e.errno == errno.ENOENT:
                return False

        return True

    @validate_absolute
    def remove(self, path):
        """Remove the given file path.

        Args:
            path (str): File path which to remove.

        Raises:
            ValueError: If the given path is not absolute.
            OSError: If path is a directory.
        """
        if self.is_local:
            return os.remove(path)
        return self._sftp.remove(path)

    @validate_absolute
    def rmdir(self, path):
        """Remove the given directory path.

        Args:
            path (str): Directory path which to remove.

        Raises:
            ValueError: If the given path is not absolute.
            OSError: If the directory is not empty.
        """
        if self.is_local:
            return os.rmdir(path)
        return self._sftp.rmdir(path)

    @validate_absolute
    def rrmdir(self, path):
        """Remove the entire directory tree.
           On remote connections `rm -rf` is used for performance reasons.

        Args:
            path (str): Directory path which to remove.

        Raises:
            ValueError: If the given path is not absolute.
        """
        if self.is_local:
            return shutil.rmtree(path)

        # Using `IO.walk` to delete all files/folders is EXTREMLY slow
        # over sftp (even to localhost connections).
        res = self._ssh.exec_command('rm -rf \'{}\''.format(path))

        # Block until execution finished
        res[1].channel.recv_exit_status()

    @validate_absolute
    def calculate_size(self, path):
        """Calculate the size of the given path.

        Args:
            path (str): Directory or file path for which to calculate the size.

        Returns:
            int: The size of the directory in bytes.

        Raises:
            ValueError: If the given path is not absolute.
            OSError: If the directory is not empty.
        """
        if self.is_local:
            res = subprocess.check_output(['du', '-s', path])
        else:
            res = self._ssh.exec_command('du -s \'{}\''.format(path))
            res = res[1].read()

        return int(res.decode().split('\t')[0]) * 1024

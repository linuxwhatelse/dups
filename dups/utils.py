import datetime
import errno
import functools
import logging
import logging.handlers
import os
import shutil
import stat
from typing import TypeVar

import paramiko

from . import config, const

import gi  # isort:skip
gi.require_version('Notify', '0.7')  # isort:skip
from gi.repository import Notify  # noqa: E402 isort:skip

Notify.init(const.DBUS_NAME)

_IO = TypeVar('_IO', bound='IO')


def add_logging_handler(file_name):
    """Add logging handler for all configured loggers.

    Args:
        file_name (str): The file name to write logs into.
    """
    cfg = config.Config.get()

    logfile = os.path.join(const.CACHE_DIR, file_name)
    do_rollover = os.path.exists(logfile)

    handler = logging.handlers.RotatingFileHandler(logfile, backupCount=7)

    if do_rollover:
        handler.doRollover()

    for name, level in cfg.logging.items():
        logging.getLogger(name).addHandler(handler)


def notify(title, body=None, icon=None, app_name=None):
    """Send a new notification to a notification daemon.

    Args:
        title (str): The notifications title.
        body (str): The notifications body.
        icon (str): Name or path of the notifications icon.
    """
    noti = Notify.Notification.new(title, body, icon)
    if app_name:
        noti.set_app_name(app_name)
    try:
        noti.show()
    except Exception:
        # Gnome  (and maybe others) throw weird erros which we have to
        # catch for now:
        # https://bugzilla.redhat.com/show_bug.cgi?id=1260239
        pass


def dict_merge(defaults, new):
    """Recursively merge two dictionaries.

    Args:
        defaults (dict): Default values.
        new (dict): New values to merge into `defaults`.

    Returns:
        dict: Merged version of both dictionaries.
    """
    for k, v in new.items():
        if (k in defaults and isinstance(defaults[k], dict)
                and isinstance(new[k], dict)):
            dict_merge(defaults[k], new[k])

        else:
            defaults[k] = new[k]

    return defaults


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
    """Decorator which validates each argument if it's a absolute path."""

    @functools.wraps(func)
    def wrapper(*args):
        for arg in args:
            if not isinstance(arg, str):
                continue
            if not os.path.isabs(arg):
                raise ValueError('Should be an absolute path!')
        return func(*args)

    return wrapper


class IO:
    """Class to abstract simple file operations for local and sftp."""
    __instances = dict()

    _instance_key = None

    _ssh = None
    _sftp = None

    def __init__(self, host=None, port=None, username=None, config_file=None,
                 key_file=None):
        """Create a new instance of `IO`_.
           Using `IO.get`_ is the preferred method.

        Args:
            See `IO.get`_ for a description of the arguments.

        Raises:
            ValueError: If an invalid `key_file` was supplied while being
                a remote instance.
        """

        self._host = host
        self._port = port
        self._username = username
        self._config_file = config_file
        self._key_file = key_file

        self._connect_remote()

    def __del__(self):
        if self._ssh:
            self._ssh.close()

        if self._instance_key in IO.__instances:
            del IO.__instances[self._instance_key]

    @classmethod
    def get(cls, host=None, port=None, username=None, config_file=None,
            key_file=None) -> _IO:
        """Get a instance of `IO`_ for the given arguments.

        Args:
            host (str): If remote, the host to connect to.
            port (int): If remote, the port on which to connect to.
            username (str): If remote, the username with wich to connect.
            key_file (str): If remote, the absolute path a ssh private key
                file to allow password-less authentication.

        Returns:
            IO: A existing (or new if it's the first call)
                instance of `IO`_ for the given arguments.
        """
        key = '{}_{}_{}_{}'.format(host, port, username, config_file, key_file)

        if key not in cls.__instances:
            cls.__instances[key] = cls(host, port, username, config_file,
                                       key_file)

        cls.__instances[key]._instance_key = key
        return cls.__instances[key]

    def _connect_remote(self):
        """Connect to the remote host."""
        if self.is_local:
            return

        self._ssh = paramiko.client.SSHClient()

        self._ssh.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
        self._ssh.load_system_host_keys()

        ssh_config = paramiko.SSHConfig()

        cfg = {
            'hostname': self.host,
            'port': self.port,
            'user': self.username,
            'identityfile': self.key_file
        }

        if self.config_file:
            if os.path.exists(self.config_file):
                with open(self.config_file) as f:
                    ssh_config.parse(f)

            cfg = {**cfg, **ssh_config.lookup(self.host)}

        self._host = cfg['hostname']
        self._port = cfg['port']
        self._username = cfg['user']
        self._key_file = cfg['identityfile']

        self._ssh.connect(self.host, self.port, self.username,
                          key_filename=self.key_file)

        self._sftp = self._ssh.open_sftp()

    @property
    def host(self):
        """str: The host provided while creating this instance."""
        return self._host

    @property
    def port(self):
        """int: The port provided while creating this instance."""
        return self._port

    @property
    def username(self):
        """str: The username provided while creating this instance."""
        return self._username

    @property
    def password(self):
        """str: The password provided while creating this instance."""
        return self._password

    @property
    def config_file(self):
        """str: The key_file provided while creating this instance."""
        return self._config_file

    @property
    def key_file(self):
        """str: The key_file provided while creating this instance."""
        return self._key_file

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
    def islink(self, path):
        """Test if the given path is a symbolic link.

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
            return os.path.islink(path)

        try:
            return stat.S_ISLNK(self._sftp.lstat(path).st_mode)
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

    def __sftp_walk(self, remotepath):
        """Implements `os.path.walk`_ behaviour for sftp.

        Yields:
            tuple: A 3-tuple (dirpath, dirnames, filenames).
        """
        path = remotepath
        files, folders = list(), list()

        for f in self._sftp.listdir_attr(remotepath):
            if stat.S_ISDIR(f.st_mode):
                folders.append(f.filename)
            else:
                files.append(f.filename)

        yield path, folders, files
        for folder in folders:
            new_path = os.path.join(remotepath, folder)
            for x in self.__sftp_walk(new_path):
                yield x

    @validate_absolute
    def walk(self, path):
        """Generate the file names in a directory tree by walking the tree.

        Yields:
            tuple: A 3-tuple (dirpath, dirnames, filenames).

        Raises:
            ValueError: If the given path is not absolute.
        """

        if self.is_local:
            yield from os.walk(path)
        else:
            yield from self.__sftp_walk(path)

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
    def symlink(self, src, dst):
        """Create a symbolic link pointing to src named dst.

        Args:
            src (str): Source for the symbolic link.
            dst (str): Destination for the symbolic link.

        Raises:
            ValueError: If the given path is not absolute.
        """
        if self.is_local:
            return os.symlink(src, dst)
        return self._sftp.symlink(src, dst)

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

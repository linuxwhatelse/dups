import os
import stat
import errno
import functools

import paramiko


SSH_KNOWN_HOSTS_PATH = os.path.expanduser('~/.ssh/known_hosts')


def dict_merge(defaults, new):
    """Recursive merge of two dictionaries.

    Args:
        defaults (dict): Default values.
        new (dict): New values to merge into `defaults`_

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


def valide_absolute(func):
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
    __instances = dict()

    _instance_key = None

    _transport = None
    _sftp = None

    def __init__(self, host=None, port=None, username=None, key_file=None):
            if host and port:
                if not key_file or not os.path.isfile(key_file):
                    raise ValueError('Invalid ssh key file specified.')

            self._host = host
            self._port = port
            self._username = username
            self._key_file = key_file

            self._connect_sftp(host, port, username, key_file)

    def __del__(self):
        if self._transport:
            self._transport.close()

        if self._instance_key in IO.__instances:
            del IO.__instances[self._instance_key]

    @classmethod
    def get(cls, host=None, port=None, username=None, key_file=None):
        key = '{}_{}_{}_{}'.format(host, port, username, key_file)

        if key not in cls.__instances:
            cls.__instances[key] = cls(host, port, username, key_file)

        cls.__instances[key]._instance_key = key
        return cls.__instances[key]

    def _connect_sftp(self, host, port, username, key_file=None):
        try:
            host_keys = paramiko.util.load_host_keys(SSH_KNOWN_HOSTS_PATH)
            hostkeytype = host_keys[host].keys()[0]
            hostkey = host_keys[host][hostkeytype]

        except IOError:
            hostkey = None

        self._transport = paramiko.Transport((host, port))

        if key_file:
            ssh_key = paramiko.RSAKey.from_private_key_file(key_file)
            self._transport.connect(hostkey, username, pkey=ssh_key)
        else:
            self._transport.connect(hostkey, username)

        self._sftp = paramiko.SFTPClient.from_transport(self._transport)

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def key_file(self):
        return self._key_file

    def is_local(self):
        return self._sftp is None

    @valide_absolute
    def isfile(self, path):
        if self.is_local():
            return os.path.isfile(path)

        try:
            return stat.S_ISREG(self._sftp.stat(path).st_mode)
        except FileNotFoundError:
            return False

    @valide_absolute
    def islink(self, path):
        if self.is_local():
            return os.path.islink(path)

        try:
            return stat.S_ISLNK(self._sftp.lstat(path).st_mode)
        except FileNotFoundError:
            return False

    @valide_absolute
    def isdir(self, path):
        if self.is_local():
            return os.path.isdir(path)

        try:
            return stat.S_ISDIR(self._sftp.stat(path).st_mode)
        except FileNotFoundError:
            return False

    @valide_absolute
    def listdir(self, path):
        if self.is_local():
            return os.listdir(path)
        return self._sftp.listdir(path)

    def __sftp_walk(self, remotepath):
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

    @valide_absolute
    def walk(self, path):
        if self.is_local():
            yield from os.path.walk()
        else:
            yield from self.__sftp_walk(path)

    @valide_absolute
    def mkdir(self, path):
        if self.is_local():
            return os.mkdir(path)
        return self._sftp.mkdir(path)

    @valide_absolute
    def makedirs(self, path):
        if self.is_local():
            return os.makedirs(path)

        current = '/'
        for p in path.split('/'):
            current = os.path.join(current, p)
            if self.exists(current):
                continue
            self._sftp.mkdir(current)

    def symlink(self, source, link_name):
        if self.is_local():
            return os.symlink(source, link_name)
        return self._sftp.symlink(source, link_name)

    @valide_absolute
    def touch(self, path):
        if self.is_local():
            return open(path, 'a').close()
        return self._sftp.open(path, 'a').close()

    @valide_absolute
    def exists(self, path):
        if self.is_local():
            return os.path.exists(path)

        try:
            self._sftp.stat(path)
        except IOError as e:
            if e.errno == errno.ENOENT:
                return False
        return True

    @valide_absolute
    def remove(self, path):
        if self.is_local():
            return os.remove(path)
        return self._sftp.remove(path)

    @valide_absolute
    def rmdir(self, path):
        if self.is_local():
            return os.rmdir(path)
        return self._sftp.rmdir(path)

    @valide_absolute
    def rrmdir(self, path):
        for f in self.listdir(path):
            filepath = os.path.join(path, f)

            if self.isfile(filepath) or self.islink(filepath):
                self.remove(filepath)

            elif self.isdir(filepath):
                self.rrmdir(filepath)

        self.rmdir(path)

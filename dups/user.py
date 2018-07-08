import getpass
import grp
import os
import pwd
from typing import TypeVar

_USER = TypeVar('_USER', bound='User')


class User(object):
    __instance = None

    def __init__(self):
        self.user = getpass.getuser()

    @classmethod
    def get(cls) -> _USER:
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def set_user(self, user):
        try:
            pwd.getpwnam(user)
            self.user = user

        except KeyError:
            raise ValueError('Invalid user')

    @property
    def uid(self):
        return pwd.getpwnam(self.user).pw_uid

    @property
    def gid(self):
        return grp.getgrnam(self.user).gr_gid

    @property
    def home(self):
        return os.path.expanduser('~{}'.format(self.user))

    @property
    def config_dir(self):
        return os.path.join(self.home, '.config', 'dups')

    @property
    def config_file(self):
        return os.path.join(self.config_dir, 'config.yaml')

    @property
    def env_file(self):
        return os.path.join(self.config_dir, 'env.json')

    @property
    def cache_dir(self):
        return os.path.join(self.home, '.cache', 'dups')

    @property
    def xdg_runtime_dir(self):
        return os.path.join('/run/user', str(self.uid))

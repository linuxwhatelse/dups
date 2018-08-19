import getpass
import grp
import os
import pwd
from typing import TypeVar

_USER = TypeVar('_USER', bound='User')


class User(object):
    def __init__(self, user=None):
        if user is None:
            self.__user = getpass.getuser()
        else:
            try:
                pwd.getpwnam(user)
                self.__user = user

            except KeyError:
                raise ValueError('User "{}" is invalid.'.format(user))

    @property
    def user(self):
        return self.__user

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

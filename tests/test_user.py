import context  # noqa: F401, isort:skip

from dups import user

import pytest


class Test_User:
    def test_valid(self):
        usr = user.User('root')

        assert usr.user == 'root'
        assert usr.uid == 0
        assert usr.gid == 0
        assert usr.home == '/root'
        assert usr.config_dir == '/root/.config/dups'
        assert usr.config_file == '/root/.config/dups/config.yaml'
        assert usr.cache_dir == '/root/.cache/dups'
        assert usr.xdg_runtime_dir == '/run/user/0'

    def test_invalid(self):
        with pytest.raises(ValueError):
            user.User('__invalid__')

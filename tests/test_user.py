import context  # noqa: F401, isort:skip

import unittest

from dups import user


class Test_User(unittest.TestCase):
    def test_valid(self):
        usr = user.User('root')

        self.assertEqual(usr.user, 'root')
        self.assertEqual(usr.uid, 0)
        self.assertEqual(usr.gid, 0)
        self.assertEqual(usr.home, '/root')
        self.assertEqual(usr.config_dir, '/root/.config/dups')
        self.assertEqual(usr.config_file, '/root/.config/dups/config.yaml')
        self.assertEqual(usr.cache_dir, '/root/.cache/dups')
        self.assertEqual(usr.xdg_runtime_dir, '/run/user/0')

    def test_invalid(self):
        self.assertRaises(ValueError, user.User, '__invalid__')


if __name__ == '__main__':
    unittest.main(exit=False)

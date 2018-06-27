import context  # noqa: F401, isort:skip

import os
import shutil
import unittest

import paramiko

from dups import utils


class Test_IO(unittest.TestCase):
    @property
    def io_local(self):
        return utils.IO.get()

    @property
    def io_remote(self):
        return utils.IO.get(context.SSH_HOST, context.SSH_PORT,
                            context.SSH_USER, context.SSH_CONFIG,
                            context.SSH_KEY)

    def test_is_local(self):
        self.assertTrue(self.io_local.is_local)
        self.assertTrue(not self.io_remote.is_local)

    def test_invalid_remote(self):
        self.assertRaises(
            (OSError, paramiko.ssh_exception.NoValidConnectionsError),
            utils.IO.get, context.SSH_HOST, 23)

    def test_validate_absolute(self):
        @utils.validate_absolute
        def test(path):
            pass

        self.assertRaises(ValueError, test, '.')

    def test_isfile(self):
        # Test for local
        self.assertTrue(not self.io_local.isfile(context.TEST_DIR))
        self.assertTrue(self.io_local.isfile(context.TEST_FILE))

        # Test for remote
        self.assertTrue(not self.io_remote.isfile(context.TEST_DIR))
        self.assertTrue(self.io_remote.isfile(context.TEST_FILE))

    def test_isdir(self):
        # Test for local
        self.assertTrue(self.io_local.isdir(context.TEST_DIR))
        self.assertTrue(not self.io_local.isdir(context.TEST_FILE))

        # Test for remote
        self.assertTrue(self.io_remote.isdir(context.TEST_DIR))
        self.assertTrue(not self.io_remote.isdir(context.TEST_FILE))

    def test_listdir(self):
        files = ['dir1', 'dir2', 'file1', 'file2']

        # Test for local
        self.assertCountEqual(files, self.io_local.listdir(context.TEST_DIR))

        # Test for remote
        self.assertCountEqual(files, self.io_remote.listdir(context.TEST_DIR))

    def test_mkdir(self):
        # Test for local
        self.io_local.mkdir(context.TMP_DIR)
        self.assertTrue(os.path.isdir(context.TMP_DIR))

        # Cleanup
        shutil.rmtree(context.TMP_DIR)
        self.assertTrue(not os.path.isdir(context.TMP_DIR))

        # Test for remote
        self.io_remote.mkdir(context.TMP_DIR)
        self.assertTrue(os.path.isdir(context.TMP_DIR))

        # Cleanup
        shutil.rmtree(context.TMP_DIR)
        self.assertTrue(not os.path.exists(context.TMP_DIR))

    def test_makedirs(self):
        nested = os.path.join(context.TMP_DIR, 'nested', 'dir')

        # Test for local
        self.io_local.makedirs(nested)
        self.assertTrue(os.path.isdir(nested))

        # Cleanup
        shutil.rmtree(context.TMP_DIR)
        self.assertTrue(not os.path.exists(context.TMP_DIR))

        # Test for remote
        self.io_remote.makedirs(nested)
        self.assertTrue(os.path.isdir(nested))

        # Cleanup
        shutil.rmtree(context.TMP_DIR)
        self.assertTrue(not os.path.isdir(context.TMP_DIR))

    def test_touch(self):
        # Test for local
        self.io_local.touch(context.TMP_FILE)
        self.assertTrue(os.path.isfile(context.TMP_FILE))

        # Cleanup
        os.remove(context.TMP_FILE)
        self.assertTrue(not os.path.exists(context.TMP_FILE))

        # Test for remote
        self.io_remote.touch(context.TMP_FILE)
        self.assertTrue(os.path.isfile(context.TMP_FILE))

        # Cleanup
        os.remove(context.TMP_FILE)
        self.assertTrue(not os.path.exists(context.TMP_FILE))

    def test_exists(self):
        # Test for local
        self.assertTrue(self.io_local.exists(context.TEST_FILE))
        self.assertTrue(not self.io_local.exists(context.TMP_FILE))

        # Test for remote
        self.assertTrue(self.io_remote.exists(context.TEST_FILE))
        self.assertTrue(not self.io_remote.exists(context.TMP_FILE))

    def test_remove(self):
        # Test for local
        open(context.TMP_FILE, 'a').close()
        self.assertTrue(os.path.exists(context.TMP_FILE))
        self.io_local.remove(context.TMP_FILE)
        self.assertTrue(not os.path.exists(context.TMP_FILE))

        # Test for local
        open(context.TMP_FILE, 'a').close()
        self.assertTrue(os.path.exists(context.TMP_FILE))
        self.io_remote.remove(context.TMP_FILE)
        self.assertTrue(not os.path.exists(context.TMP_FILE))

    def test_rmdir(self):
        # Test for local
        os.makedirs(context.TMP_DIR)
        self.assertTrue(os.path.exists(context.TMP_DIR))
        self.io_local.rmdir(context.TMP_DIR)
        self.assertTrue(not os.path.exists(context.TMP_DIR))

        # Test for remote
        os.makedirs(context.TMP_DIR)
        self.assertTrue(os.path.exists(context.TMP_DIR))
        self.io_remote.rmdir(context.TMP_DIR)
        self.assertTrue(not os.path.exists(context.TMP_DIR))

    def test_rrmdir(self):
        nested = os.path.join(context.TMP_DIR, 'nested', 'dir')

        # Test for local
        os.makedirs(nested)
        self.assertTrue(os.path.exists(nested))
        self.io_local.rrmdir(context.TMP_DIR)
        self.assertTrue(not os.path.exists(context.TMP_DIR))

        # Test for remote
        os.makedirs(nested)
        self.assertTrue(os.path.exists(nested))
        self.io_remote.rrmdir(context.TMP_DIR)
        self.assertTrue(not os.path.exists(context.TMP_DIR))


if __name__ == '__main__':
    unittest.main(exit=False)

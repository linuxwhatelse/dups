import context  # noqa: F401, isort:skip

import os
import shutil
import unittest

from dups import utils

from ddt import data, ddt


@ddt
class Test_IO(unittest.TestCase):
    def tearDown(self):
        if os.path.exists(context.TMP_DIR):
            shutil.rmtree(context.TMP_DIR)

        if os.path.exists(context.TMP_FILE):
            os.remove(context.TMP_FILE)

    def get_io(self, target):
        if target is 'local':
            return utils.IO.get()
        elif target == 'remote':
            return utils.IO.get(context.SSH_HOST)
        return None

    @data('local', 'remote')
    def test_is_local(self, target):
        io = self.get_io(target)

        if target is 'local':
            self.assertTrue(io.is_local)
        elif target is 'remote':
            self.assertTrue(not io.is_local)

        io.close()

    def test_invalid(self):
        self.assertRaises(Exception, utils.IO.get, context.SSH_HOST,
                          context.SSH_CONFIG_INVALID)

    def test_validate_absolute(self):
        @utils.validate_absolute
        def test(path):
            pass

        self.assertRaises(ValueError, test, '.')

    @data('local', 'remote')
    def test_isfile(self, target):
        io = self.get_io(target)

        self.assertTrue(not io.isfile(context.TEST_DIR))
        self.assertTrue(io.isfile(context.TEST_FILE))

        io.close()

    @data('local', 'remote')
    def test_isdir(self, target):
        io = self.get_io(target)

        self.assertTrue(io.isdir(context.TEST_DIR))
        self.assertTrue(not io.isdir(context.TEST_FILE))

        io.close()

    @data('local', 'remote')
    def test_listdir(self, target):
        io = self.get_io(target)

        files = ['dir1', 'dir2', 'file1', 'file2']
        self.assertCountEqual(files, io.listdir(context.TEST_DIR))

        io.close()

    @data('local', 'remote')
    def test_mkdir(self, target):
        io = self.get_io(target)

        io.mkdir(context.TMP_DIR)
        self.assertTrue(os.path.isdir(context.TMP_DIR))

        io.close()

    @data('local', 'remote')
    def test_makedirs(self, target):
        io = self.get_io(target)

        nested = os.path.join(context.TMP_DIR, 'nested', 'dir')

        io.makedirs(nested)
        self.assertTrue(os.path.isdir(nested))

        io.close()

    @data('local', 'remote')
    def test_touch(self, target):
        io = self.get_io(target)

        io.touch(context.TMP_FILE)
        self.assertTrue(os.path.isfile(context.TMP_FILE))

        io.close()

    @data('local', 'remote')
    def test_exists(self, target):
        io = self.get_io(target)

        self.assertTrue(io.exists(context.TEST_FILE))
        self.assertTrue(not io.exists(context.TMP_FILE))

        io.close()

    @data('local', 'remote')
    def test_remove(self, target):
        io = self.get_io(target)

        open(context.TMP_FILE, 'a').close()
        self.assertTrue(os.path.exists(context.TMP_FILE))
        io.remove(context.TMP_FILE)
        self.assertTrue(not os.path.exists(context.TMP_FILE))

        io.close()

    @data('local', 'remote')
    def test_rmdir(self, target):
        io = self.get_io(target)

        os.makedirs(context.TMP_DIR)
        self.assertTrue(os.path.exists(context.TMP_DIR))
        io.rmdir(context.TMP_DIR)
        self.assertTrue(not os.path.exists(context.TMP_DIR))

        io.close()

    @data('local', 'remote')
    def test_rrmdir(self, target):
        io = self.get_io(target)

        nested = os.path.join(context.TMP_DIR, 'nested', 'dir')
        os.makedirs(nested)

        self.assertTrue(os.path.exists(nested))
        io.rrmdir(context.TMP_DIR)
        self.assertTrue(not os.path.exists(context.TMP_DIR))

        io.close()

    @data('local', 'remote')
    def test_open(self, target):
        io = self.get_io(target)

        msg = 'Hello dups!'
        with io.open(context.TMP_FILE, 'w') as f:
            f.write(msg)

        with open(context.TMP_FILE) as f:
            self.assertEqual(msg, f.read())


if __name__ == '__main__':
    unittest.main(exit=False)

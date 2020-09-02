import context  # noqa: F401, isort:skip

import os
import shutil
from datetime import datetime, timedelta

from dups import utils

import pytest


class Test_gffs:
    def test_rotate_gffs_weekday_6(self):
        start = datetime(2017, 12, 31)

        datetimes = []
        for i in range(365 * 6):
            datetimes.append(start - timedelta(days=i))

        gffs = utils.rotate_gffs(datetimes, days=7, weeks=4, months=12,
                                 years=3, weekday_full=6)

        assert gffs[4] == [
            # Years
            datetime(2013, 12, 29),
            datetime(2014, 12, 28),
            datetime(2015, 12, 27),
            # Months
            datetime(2016, 12, 25),
            datetime(2017, 1, 29),
            datetime(2017, 2, 26),
            datetime(2017, 3, 26),
            datetime(2017, 4, 30),
            datetime(2017, 5, 28),
            datetime(2017, 6, 25),
            datetime(2017, 7, 30),
            datetime(2017, 8, 27),
            datetime(2017, 9, 24),
            datetime(2017, 10, 29),
            datetime(2017, 11, 26),
            # Weeks
            datetime(2017, 12, 3),
            datetime(2017, 12, 10),
            datetime(2017, 12, 17),
            datetime(2017, 12, 24),
            # Days
            datetime(2017, 12, 25),
            datetime(2017, 12, 26),
            datetime(2017, 12, 27),
            datetime(2017, 12, 28),
            datetime(2017, 12, 29),
            datetime(2017, 12, 30),
            datetime(2017, 12, 31),
        ]

    def test_rotate_gffs_weekday_0(self):
        start = datetime(2017, 12, 31)

        datetimes = []
        for i in range(365 * 7):
            datetimes.append(start - timedelta(days=i))

        gffs = utils.rotate_gffs(datetimes, days=7, weeks=4, months=12,
                                 years=3, weekday_full=0)

        assert gffs[4] == [
            # Years
            datetime(2013, 12, 30),
            datetime(2014, 12, 29),
            datetime(2015, 12, 28),
            # Months
            datetime(2016, 11, 28),
            datetime(2016, 12, 26),
            datetime(2017, 1, 30),
            datetime(2017, 2, 27),
            datetime(2017, 3, 27),
            datetime(2017, 4, 24),
            datetime(2017, 5, 29),
            datetime(2017, 6, 26),
            datetime(2017, 7, 31),
            datetime(2017, 8, 28),
            datetime(2017, 9, 25),
            datetime(2017, 10, 30),
            # Weeks
            datetime(2017, 11, 27),
            datetime(2017, 12, 4),
            datetime(2017, 12, 11),
            datetime(2017, 12, 18),
            # Days
            datetime(2017, 12, 25),
            datetime(2017, 12, 26),
            datetime(2017, 12, 27),
            datetime(2017, 12, 28),
            datetime(2017, 12, 29),
            datetime(2017, 12, 30),
            datetime(2017, 12, 31),
        ]


class Test_IO:
    TMP_FILE = os.path.join(context.HERE, 'tmp.file')
    TEST_FILE = os.path.join(context.DATA_DIR, 'test.file')
    TEST_DIR = os.path.join(context.DATA_DIR, 'test.dir')

    def teardown_method(self, method):
        if os.path.exists(context.TMP_DIR):
            shutil.rmtree(context.TMP_DIR)

        if os.path.exists(Test_IO.TMP_FILE):
            os.remove(Test_IO.TMP_FILE)

    def get_io(self, target):
        if target == 'local':
            return utils.IO.get()
        elif target == 'remote':
            return utils.IO.get(context.SSH_HOST)
        return None

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_is_local(self, target):
        io = self.get_io(target)

        if target == 'local':
            assert io.is_local
        elif target == 'remote':
            assert not io.is_local

        io.close()

    def test_validate_absolute(self):
        @utils.validate_absolute
        def test(path):
            pass

        with pytest.raises(ValueError):
            test('.')

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_isfile(self, target):
        io = self.get_io(target)

        assert not io.isfile(Test_IO.TEST_DIR)
        assert io.isfile(Test_IO.TEST_FILE)

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_isdir(self, target):
        io = self.get_io(target)

        assert io.isdir(Test_IO.TEST_DIR)
        assert not io.isdir(Test_IO.TEST_FILE)

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_listdir(self, target):
        io = self.get_io(target)

        files = ['dir1', 'dir2', 'file1', 'file2']
        assert len(files) == len(io.listdir(Test_IO.TEST_DIR))

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_mkdir(self, target):
        io = self.get_io(target)

        io.mkdir(context.TMP_DIR)
        assert os.path.isdir(context.TMP_DIR)

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_makedirs(self, target):
        io = self.get_io(target)

        nested = os.path.join(context.TMP_DIR, 'nested', 'dir')

        io.makedirs(nested)
        assert os.path.isdir(nested)

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_touch(self, target):
        io = self.get_io(target)

        io.touch(Test_IO.TMP_FILE)
        assert os.path.isfile(Test_IO.TMP_FILE)

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_exists(self, target):
        io = self.get_io(target)

        assert io.exists(Test_IO.TEST_FILE)
        assert not io.exists(Test_IO.TMP_FILE)

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_remove(self, target):
        io = self.get_io(target)

        open(Test_IO.TMP_FILE, 'a').close()
        assert os.path.exists(Test_IO.TMP_FILE)
        io.remove(Test_IO.TMP_FILE)
        assert not os.path.exists(Test_IO.TMP_FILE)

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_rmdir(self, target):
        io = self.get_io(target)

        os.makedirs(context.TMP_DIR)
        assert os.path.exists(context.TMP_DIR)
        io.rmdir(context.TMP_DIR)
        assert not os.path.exists(context.TMP_DIR)

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_rrmdir(self, target):
        io = self.get_io(target)

        nested = os.path.join(context.TMP_DIR, 'nested', 'dir')
        os.makedirs(nested)

        assert os.path.exists(nested)
        io.rrmdir(context.TMP_DIR)
        assert not os.path.exists(context.TMP_DIR)

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_open(self, target):
        io = self.get_io(target)

        msg = 'Hello dups!'
        with io.open(Test_IO.TMP_FILE, 'w') as f:
            f.write(msg)

        with open(Test_IO.TMP_FILE) as f:
            assert msg == f.read()

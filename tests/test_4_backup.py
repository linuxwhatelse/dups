import context  # noqa: F401, isort:skip
import json
import os
import shutil
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

from dups import backup, exceptions, rsync, utils

import pytest
import testutils


class Test_Backup:
    __start_dir = os.getcwd()

    def setup_method(self, method):
        os.makedirs(context.TARGET_DIR)
        os.makedirs(context.TMP_DIR)

    def teardown_method(self, method):
        os.chdir(self.__start_dir)

        for dir_ in (context.TARGET_DIR, context.TMP_DIR):
            if os.path.isdir(dir_):
                shutil.rmtree(dir_)

    @contextmanager
    def _io(self, target):
        io = None
        try:
            if target is 'local':
                io = utils.IO.get()
            elif target == 'remote':
                io = utils.IO.get('localhost')
            yield io

        finally:
            if io:
                io.close()

    def _create_backup(self, name, valid, data=None):
        os.chdir(context.TARGET_DIR)

        if not data:
            data = {}

        testutils.create_dir_struct({
            name: {
                'data': data,
            },
        })

        with open(os.path.join(name, '.info'), 'w') as f:
            f.write(json.dumps({'valid': valid}))

        os.chdir(self.__start_dir)

    def _create_test_data(self, target_dir):
        tmp = os.getcwd()

        os.chdir(target_dir)
        testutils.create_dir_struct({
            'simple.file': None,
            'simple folder': {},
            'special * folder': {},
            r'''!"#$%&'()*+,-.012:;<=>?@ABC[\]^_`abc{|}~''': None
        })

        os.chdir(tmp)

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_new(self, target):
        with self._io(target) as io:
            try:
                # Should not raise any errors
                backup.Backup.new(io, context.TARGET_DIR)
            except Exception as e:
                self.fail(str(e))

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_from_name(self, target):
        self._create_backup('19900101000000', False)

        with self._io(target) as io:
            try:
                # Should not raise any errors
                backup.Backup.from_name(io, '19900101000000',
                                        context.TARGET_DIR)

            except Exception as e:
                pytest.fail(str(e))

            with pytest.raises(exceptions.BackupNotFoundException):
                backup.Backup.from_name(io, 'no_such_backup',
                                        context.TARGET_DIR)

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_all_backups(self, target):
        self._create_backup('19900101000000', True)
        self._create_backup('19900102000000', False)

        with self._io(target) as io:
            # Get a list of valid backups
            backups = backup.Backup.all_backups(io, context.TARGET_DIR,
                                                include_valid=True,
                                                include_invalid=False)
            assert len(backups) == 1

            # Get a list of all (valid and invalid) backups
            backups = backup.Backup.all_backups(io, context.TARGET_DIR,
                                                include_valid=True,
                                                include_invalid=True)
            assert len(backups) == 2

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_latest(self, target):
        self._create_backup('19900101000000', True)
        self._create_backup('19900102000000', False)

        with self._io(target) as io:
            bak = backup.Backup.latest(io, context.TARGET_DIR,
                                       include_valid=False,
                                       include_invalid=False)
            assert bak is None

            # Get the latest valid backup
            bak = backup.Backup.latest(io, context.TARGET_DIR,
                                       include_valid=True,
                                       include_invalid=False)
            valid = backup.Backup.from_name(io, '19900101000000',
                                            context.TARGET_DIR)
            assert bak == valid

            # Get the latest backup including invalid ones
            bak = backup.Backup.latest(io, context.TARGET_DIR,
                                       include_valid=True,
                                       include_invalid=True)
            invalid = backup.Backup.from_name(io, '19900102000000',
                                              context.TARGET_DIR)
            assert bak == invalid

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_backup_properties(self, target):
        self._create_backup('19900101000000', True)

        with self._io(target) as io:
            bak = backup.Backup.from_name(io, '19900101000000',
                                          context.TARGET_DIR)

            assert bak.name == '19900101000000'
            assert bak.name_pretty == '01, Jan 1990 00:00:00'
            assert bak.datetime == datetime(1990, 1, 1, 0, 0, 0)
            assert bak.backup_root_dir == context.TARGET_DIR
            assert bak.backup_dir == os.path.join(context.TARGET_DIR,
                                                  '19900101000000')
            assert bak.backup_data_dir == os.path.join(
                context.TARGET_DIR, '19900101000000', 'data')
            assert bak.info_path == os.path.join(context.TARGET_DIR,
                                                 '19900101000000', '.info')
            assert bak.exists is True
            assert bak.info == {'valid': True}
            assert bak.is_valid is True

            bak.set_valid(False)

            assert bak.info == {'valid': False}
            assert bak.is_valid is False

    @patch('dups.rsync.rsync.sync')
    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_backup_data_dir(self, mock_sync, target):
        with self._io(target) as io:
            bak = backup.Backup.new(io, context.TARGET_DIR)

            bak.backup([], dry_run=True)
            assert not os.path.exists(bak.backup_data_dir)

            bak.backup([], dry_run=False)
            assert os.path.exists(bak.backup_data_dir)

    @patch('dups.rsync.rsync.sync')
    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_backup_info_file(self, mock_sync, target):
        with self._io(target) as io:
            bak = backup.Backup.new(io, context.TARGET_DIR)

            bak.backup([], dry_run=True)
            assert not os.path.exists(bak.info_path)

            bak.backup([], dry_run=False)
            assert os.path.exists(bak.info_path)

    @patch('dups.rsync.rsync.sync')
    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_backup_args(self, mock_sync, target):
        self._create_backup('19900101000000', True)

        self._create_test_data(context.TMP_DIR)
        os.chdir(context.TMP_DIR)

        with self._io(target) as io:
            includes = [
                'simple.file',
                'simple folder',
                'special * folder',
                r'''!"#$%&'()*+,-.012:;<=>?@ABC[\]^_`abc{|}~''',
            ]
            excludes = ['simple*']

            bak = backup.Backup.new(io, context.TARGET_DIR)
            bak.backup(includes, excludes)

            args = mock_sync.call_args[0]
            assert includes == args[1]
            assert excludes == args[2]
            assert os.path.join(context.TARGET_DIR, '19900101000000',
                                'data') == args[3]

    @patch('dups.rsync.rsync.sync')
    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_restore_args(self, mock_sync, target):
        self._create_backup('19900101000000', True)

        with self._io(target) as io:
            bak = backup.Backup.from_name(io, '19900101000000',
                                          context.TARGET_DIR)

            bak.restore('/')
            args = mock_sync.call_args[0]
            assert '/' == args[0].resolved

            item = rsync.Path(bak.backup_data_dir, io.host).resolved
            item = os.path.join(item, './')
            assert item == args[1][0].resolved

    @patch('dups.utils.IO.rrmdir')
    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_remove(self, mock_rrmdir, target):
        self._create_backup('19900101000000', True)

        with self._io(target) as io:
            bak = backup.Backup.from_name(io, '19900101000000',
                                          context.TARGET_DIR)
            bak.remove()

            assert bak.backup_dir == mock_rrmdir.call_args[0][0]

            shutil.rmtree(bak.backup_dir)

            with pytest.raises(exceptions.BackupNotFoundException):
                bak.remove()

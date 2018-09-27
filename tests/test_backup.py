import context  # noqa: F401, isort:skip

import os
import shutil

from dups import backup, exceptions, utils

import pytest
import utils as test_utils


class Test_Backup:
    missing_backup = '19900100000000'
    valid_backup = '19900101000000'
    invalid_backup = '19900102000000'

    def teardown_method(self, method):
        for dir_ in os.listdir(context.BACKUP_DIR):
            if dir_ in [self.valid_backup, self.invalid_backup]:
                continue
            dir_ = os.path.join(context.BACKUP_DIR, dir_)
            shutil.rmtree(dir_)

        if os.path.exists(context.TMP_DIR):
            shutil.rmtree(context.TMP_DIR)

    def get_io(self, target):
        if target is 'local':
            return utils.IO.get()
        elif target == 'remote':
            return utils.IO.get(context.SSH_HOST)
        return None

    def get_valid(self, io):
        return backup.Backup.from_name(io, self.valid_backup,
                                       context.BACKUP_DIR)

    def get_invalid(self, io):
        return backup.Backup.from_name(io, self.invalid_backup,
                                       context.BACKUP_DIR)

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_new(self, target):
        io = self.get_io(target)

        try:
            # Should not raise any errors
            backup.Backup.new(io, context.BACKUP_DIR)
        except Exception as e:
            self.fail(str(e))

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_from_label(self, target):
        io = self.get_io(target)

        try:
            # Should not raise any errors
            self.get_valid(io)

        except Exception as e:
            pytest.fail(str(e))

        with pytest.raises(exceptions.BackupNotFoundException):
            backup.Backup.from_name(io, self.missing_backup,
                                    context.BACKUP_DIR)

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_all_backups(self, target):
        io = self.get_io(target)

        # Get a list of valid backups
        backups = backup.Backup.all_backups(io, context.BACKUP_DIR)
        assert len(backups) == 1

        # Get a list of all (valid and invalid) backups
        backups = backup.Backup.all_backups(io, context.BACKUP_DIR, True, True)
        assert len(backups) == 2

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_latest(self, target):
        io = self.get_io(target)

        # Get the latest valid backup
        bak = backup.Backup.latest(io, context.BACKUP_DIR)
        assert self.get_valid(io) == bak

        # Get the latest backup including invalid ones
        bak = backup.Backup.latest(io, context.BACKUP_DIR, True, True)
        assert self.get_invalid(io) == bak

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_backup(self, target):
        io = self.get_io(target)

        bak = backup.Backup.new(io, context.BACKUP_DIR)
        status = bak.backup([context.TEST_DIR, context.TEST_FILE],
                            excludes=['**/dir2/.gitkeep'])

        assert status.exit_code == 0
        assert os.path.exists(bak.backup_data_dir)

        # Define the structure we expect after the backup
        expected_data = test_utils.get_dir_struct(context.DATA_DIR)

        del expected_data['test.dir']['dir2']

        real_data_dir = os.path.join(bak.backup_data_dir,
                                     context.DATA_DIR.lstrip('/'))

        synced_data = test_utils.get_dir_struct(real_data_dir)
        assert expected_data == synced_data

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_backup_pattern(self, target):
        io = self.get_io(target)

        bak = backup.Backup.new(io, context.BACKUP_DIR)
        status = bak.backup([os.path.join(context.DATA_DIR, 'test*')],
                            excludes=['**/dir2'])

        assert status.exit_code == 0

        # Define the structure we expect after the backup
        expected_data = test_utils.get_dir_struct(context.DATA_DIR)
        del expected_data['test.dir']['dir2']

        real_data_dir = os.path.join(bak.backup_data_dir,
                                     context.DATA_DIR.lstrip('/'))

        synced_data = test_utils.get_dir_struct(real_data_dir)
        assert expected_data == synced_data

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_backup_dry_run(self, target):
        io = self.get_io(target)

        bak = backup.Backup.new(io, context.BACKUP_DIR)
        status = bak.backup([context.TEST_DIR, context.TEST_FILE],
                            dry_run=True)

        assert status.exit_code == 0
        assert not os.path.exists(bak.backup_dir)

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_restore_items(self, target):
        io = self.get_io(target)

        bak = self.get_valid(io)
        status = bak.restore(context.TMP_DIR, ['/tmp/test1.file'])

        assert status.exit_code == 0

        expected_data = test_utils.get_dir_struct(bak.backup_data_dir)
        del expected_data['tmp']['test2.file']
        del expected_data['tmp']['test3.file']

        synced_data = test_utils.get_dir_struct(context.TMP_DIR)
        assert expected_data == synced_data

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_restore_full(self, target):
        io = self.get_io(target)

        bak = self.get_valid(io)
        status = bak.restore(context.TMP_DIR)

        assert status.exit_code == 0

        expected_data = test_utils.get_dir_struct(bak.backup_data_dir)
        synced_data = test_utils.get_dir_struct(context.TMP_DIR)
        assert expected_data == synced_data

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_restore_dry_run(self, target):
        io = self.get_io(target)

        bak = self.get_valid(io)
        status = bak.restore(context.TMP_DIR, dry_run=True)

        assert status.exit_code == 0
        assert not os.path.exists(context.TMP_DIR)

        io.close()

    @pytest.mark.parametrize('target', ['local', 'remote'])
    def test_remove(self, target):
        io = self.get_io(target)

        bak = backup.Backup.new(io, context.BACKUP_DIR)
        bak.backup([context.TEST_FILE])

        assert os.path.exists(bak.backup_data_dir)
        bak.remove()
        assert not os.path.exists(bak.backup_data_dir)

        io.close()

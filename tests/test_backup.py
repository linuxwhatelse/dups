import context  # noqa: F401, isort:skip

import os
import shutil
import unittest

from dups import backup, exceptions, utils

import utils as test_utils
from ddt import data, ddt


@ddt
class Test_Backup(unittest.TestCase):
    missing_backup = '19900100000000'
    valid_backup = '19900101000000'
    invalid_backup = '19900102000000'

    def tearDown(self):
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
            return utils.IO.get(context.SSH_HOST, context.SSH_PORT,
                                context.SSH_USER)
        return None

    def get_valid(self, io):
        return backup.Backup.from_name(io, self.valid_backup,
                                       context.BACKUP_DIR)

    def get_invalid(self, io):
        return backup.Backup.from_name(io, self.invalid_backup,
                                       context.BACKUP_DIR)

    @data('local', 'remote')
    def test_new(self, target):
        io = self.get_io(target)

        try:
            # Should not raise any errors
            backup.Backup.new(io, context.BACKUP_DIR)
        except Exception as e:
            self.fail(str(e))

    @data('local', 'remote')
    def test_from_label(self, target):
        io = self.get_io(target)

        try:
            # Should not raise any errors
            self.get_valid(io)

        except Exception as e:
            self.fail(str(e))

        self.assertRaises(exceptions.BackupNotFoundException,
                          backup.Backup.from_name, io, self.missing_backup,
                          context.BACKUP_DIR)

    @data('local', 'remote')
    def test_all_backups(self, target):
        io = self.get_io(target)

        # Get a list of valid backups
        backups = backup.Backup.all_backups(io, context.BACKUP_DIR)
        self.assertCountEqual([self.get_valid(io)], backups)

        # Get a list of all (valid and invalid) bakcups
        backups = backup.Backup.all_backups(io, context.BACKUP_DIR, True, True)
        self.assertCountEqual(
            [self.get_valid(io), self.get_invalid(io)], backups)

    @data('local', 'remote')
    def test_latest(self, target):
        io = self.get_io(target)

        # Get the latest valid backup
        bak = backup.Backup.latest(io, context.BACKUP_DIR)
        self.assertEqual(self.get_valid(io), bak)

        # Get the latest backup including invalid ones
        bak = backup.Backup.latest(io, context.BACKUP_DIR, True, True)
        self.assertEqual(self.get_invalid(io), bak)

    @data('local', 'remote')
    def test_backup(self, target):
        io = self.get_io(target)

        bak = backup.Backup.new(io, context.BACKUP_DIR)
        status = bak.backup([context.TEST_DIR, context.TEST_FILE],
                            excludes=['**/dir2/.gitkeep'])

        self.assertEqual(status.exit_code, 0)
        self.assertTrue(os.path.exists(bak.backup_data_dir))

        # Define the structure we expect after the backup
        expected_data = test_utils.get_dir_struct(context.DATA_DIR)
        del expected_data['test.dir']['dir2']

        real_data_dir = os.path.join(bak.backup_data_dir,
                                     context.DATA_DIR.lstrip('/'))

        synced_data = test_utils.get_dir_struct(real_data_dir)
        self.assertEqual(expected_data, synced_data)

    @data('local', 'remote')
    def test_backup_dry_run(self, target):
        io = self.get_io(target)

        bak = backup.Backup.new(io, context.BACKUP_DIR)
        status = bak.backup([context.TEST_DIR, context.TEST_FILE],
                            dry_run=True)

        self.assertEqual(status.exit_code, 0)
        self.assertTrue(not os.path.exists(bak.backup_dir))

    @data('local', 'remote')
    def test_restore_items(self, target):
        io = self.get_io(target)

        bak = self.get_valid(io)
        status = bak.restore(context.TMP_DIR, ['/tmp/test1.file'])

        self.assertEqual(status.exit_code, 0)

        expected_data = test_utils.get_dir_struct(bak.backup_data_dir)
        del expected_data['tmp']['test2.file']
        del expected_data['tmp']['test3.file']

        synced_data = test_utils.get_dir_struct(context.TMP_DIR)
        self.assertEqual(expected_data, synced_data)

    @data('local', 'remote')
    def test_restore_full(self, target):
        io = self.get_io(target)

        bak = self.get_valid(io)
        status = bak.restore(context.TMP_DIR)

        self.assertEqual(status.exit_code, 0)

        expected_data = test_utils.get_dir_struct(bak.backup_data_dir)
        synced_data = test_utils.get_dir_struct(context.TMP_DIR)
        self.assertEqual(expected_data, synced_data)

    @data('local', 'remote')
    def test_restore_dry_run(self, target):
        io = self.get_io(target)

        bak = self.get_valid(io)
        status = bak.restore(context.TMP_DIR, dry_run=True)

        self.assertEqual(status.exit_code, 0)
        self.assertTrue(not os.path.exists(context.TMP_DIR))

    @data('local', 'remote')
    def test_remove(self, target):
        io = self.get_io(target)

        bak = backup.Backup.new(io, context.BACKUP_DIR)
        bak.backup([context.TEST_FILE])

        self.assertTrue(os.path.exists(bak.backup_data_dir))
        bak.remove()
        self.assertTrue(not os.path.exists(bak.backup_data_dir))


if __name__ == '__main__':
    unittest.main(exit=False)

import context  # noqa: F401, isort:skip

import os
import shlex
import shutil
from unittest.mock import patch

from dups import const, rsync

import pytest
import utils as test_utils


class Test_Path:
    def test_local(self):
        p = rsync.Path('/tmp')
        assert p.is_local

    def test_remote(self):
        p = rsync.Path('/tmp', 'localhost')
        assert not p.is_local

    def test_resolved_local(self):
        p = rsync.Path('/tmp')
        assert p.resolved == '/tmp'

    def test_resolved_remote(self):
        p = rsync.Path('/tmp', 'localhost')
        assert p.resolved == 'localhost:/tmp'


class Test_Status:
    def test_valid(self):
        status = rsync.Status(0)
        assert status.exit_code == 0

    def test_invalid(self):
        with pytest.raises(ValueError):
            rsync.Status(-999)

    def test_complete(self):
        status = rsync.Status(0)
        assert status.is_complete

    def test_incomplete(self):
        status = rsync.Status(20)
        assert not status.is_complete


class Test_rsync:
    __start_dir = os.getcwd()

    def setup_method(self, method):
        os.makedirs(context.TMP_DIR)
        os.chdir(context.TMP_DIR)

    def teardown_method(self, method):
        os.chdir(self.__start_dir)
        if os.path.isdir(context.TMP_DIR):
            shutil.rmtree(context.TMP_DIR)

    @patch('dups.rsync.rsync._exec')
    def test_options_original(self, mock_exec):
        sync = rsync.rsync()
        sync.sync(rsync.Path('/'), [])

        cmd = mock_exec.call_args[0][0]
        assert b'--acls' in cmd
        assert b'--xattrs' in cmd
        assert b'--prune-empty-dirs' in cmd
        assert b"--out-format '%t %i %n'" in cmd
        assert b'--dry-run' in cmd

    @patch('dups.rsync.rsync._exec')
    def test_options_modified(self, mock_exec):
        sync = rsync.rsync()

        sync.acls = False
        sync.xattrs = False
        sync.prune_empty_dirs = False
        sync.out_format = "%t %i %f %''b"
        sync.dry_run = False

        sync.sync(rsync.Path('/'), [])

        cmd = mock_exec.call_args[0][0]
        assert b'--acls' not in cmd
        assert b'--xattrs' not in cmd
        assert b'--prune-empty-dirs' not in cmd
        assert '--out-format {}'.format(
            shlex.quote("%t %i %f %''b")).encode() in cmd
        assert b'--dry-run' not in cmd

    @patch('dups.rsync.rsync._exec')
    def test_includes(self, mock_exec):
        test_utils.create_dir_struct({
            'simple.file': None,
            'simple folder': {},
            r'special * folder': {},
            r'''!"#$%&'()*+,-.012:;<=>?@ABC[\]^_`abc{|}~''': None
        })

        sync = rsync.rsync()
        sync.sync(
            rsync.Path(context.TMP_DIR), [
                'simple.file',
                'simple folder',
                'special * folder',
                'not found * folder',
                r'test\ \*\ folder/*.pattern',
                r'''!"#$%&'()*+,-.012:;<=>?@ABC[\]^_`abc{|}~''',
            ])

        cmd = cmd = mock_exec.call_args[0][0]
        assert b'simple.file' in cmd
        assert b"'simple folder'" in cmd
        assert b"'special * folder'" in cmd
        assert b'not found * folder' in cmd
        assert rb'test\ \*\ folder/*.pattern' in cmd
        assert b"'!"  #$%&' "'" '()*+,-.012:;<=>?@ABC[\]^_`abc{|}~'" in cmd

    @patch('dups.rsync.rsync._exec')
    def test_excludes(self, mock_exec):
        sync = rsync.rsync()
        sync.sync(
            rsync.Path(context.TMP_DIR), ['/'], [
                '/tmp',
                'simple folder',
                '*.mkv',
            ])

        cmd = mock_exec.call_args[0][0]
        assert b"--exclude /tmp" in cmd
        assert b"--exclude 'simple folder'" in cmd
        assert b"--exclude '*.mkv'" in cmd


class Test_rsync_old:
    @property
    def data_dir_struct(self):
        return test_utils.get_dir_struct(context.DATA_DIR)

    @property
    def real_target(self):
        return os.path.join(context.TMP_DIR, context.DATA_DIR.lstrip('/'))

    def teardown_method(self, method):
        if os.path.isdir(context.TMP_DIR):
            shutil.rmtree(context.TMP_DIR)

        if os.path.isfile(context.TMP_FILE):
            os.remove(context.TMP_FILE)

    def test_singleton(self):
        sync1 = rsync.rsync.get()
        sync2 = rsync.rsync.get()

        assert sync1 == sync2

        del sync2
        sync2 = None

        sync2 = rsync.rsync.get()
        assert sync1 == sync2

    def test_success(self):
        sync = rsync.rsync()
        sync.dry_run = False

        target = rsync.Path(context.TMP_DIR)
        status = sync.sync(target, [context.TEST_DIR])
        assert status.exit_code == 0

    def test_local_simple(self):
        sync = rsync.rsync()
        sync.dry_run = False

        # Define the structure we expect after synchronizing
        expected_data = self.data_dir_struct
        del expected_data['test.dir']['dir2']

        # Send the files
        target = rsync.Path(context.TMP_DIR)
        sync.sync(target, [context.TEST_DIR, context.TEST_FILE],
                  excludes=['**/dir2/.gitkeep'])

        # Get and compare the structure of our sync target
        synced_data = test_utils.get_dir_struct(self.real_target)
        assert expected_data == synced_data

    def test_remote_simple(self):
        sync = rsync.rsync()
        sync.dry_run = False

        # Define the structure we expect after synchronizing
        expected_data = self.data_dir_struct
        del expected_data['test.dir']['dir2']

        # Send the files
        target = rsync.Path(context.TMP_DIR, context.SSH_HOST)
        sync.sync(target, [context.TEST_DIR, context.TEST_FILE],
                  excludes=['**/dir2/.gitkeep'])

        # Get and compare the structure of our sync target
        synced_data = test_utils.get_dir_struct(self.real_target)
        assert expected_data == synced_data

    def test_ssh_wrapper(self):
        sync = rsync.rsync()
        sync.ssh_bin = '{} root {}'.format(const.SSH_WRAPPER_SCRIPT,
                                           sync.ssh_bin)
        sync.dry_run = False

        # Send the files
        target = rsync.Path(context.TMP_DIR, context.SSH_HOST)
        status = sync.sync(target, [context.DATA_DIR])

        assert status.exit_code == 0

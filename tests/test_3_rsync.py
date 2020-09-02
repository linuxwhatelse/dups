import context  # noqa: F401, isort:skip

import os
import shlex
import shutil
from unittest.mock import patch

from dups import rsync

import pytest
import testutils


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
        os.makedirs(context.TARGET_DIR)
        os.chdir(context.TARGET_DIR)

    def teardown_method(self, method):
        os.chdir(self.__start_dir)
        if os.path.isdir(context.TARGET_DIR):
            shutil.rmtree(context.TARGET_DIR)

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
    def test_target_local(self, mock_exec):
        sync = rsync.rsync()
        sync.sync(rsync.Path('/backup-target'), [])

        cmd = mock_exec.call_args[0][0]
        assert cmd.endswith(b'/backup-target')

    @patch('dups.rsync.rsync._exec')
    def test_target_remote(self, mock_exec):
        sync = rsync.rsync()
        sync.sync(rsync.Path('/backup-target', 'localhost'), [])

        cmd = mock_exec.call_args[0][0]
        assert cmd.endswith(b'localhost:/backup-target')

    @patch('dups.rsync.rsync._exec')
    def test_includes(self, mock_exec):
        testutils.create_dir_struct({
            'simple.file': None,
            'simple folder': {},
            'special * folder': {},
            r'''!"#$%&'()*+,-.012:;<=>?@ABC[\]^_`abc{|}~''': None
        })

        sync = rsync.rsync()
        sync.sync(rsync.Path(context.TARGET_DIR), [
            'simple.file',
            'simple folder',
            'special * folder',
            'not found * folder',
            r'test\ \*\ folder/*.pattern',
            r'''!"#$%&'()*+,-.012:;<=>?@ABC[\]^_`abc{|}~''',
        ])

        cmd = mock_exec.call_args[0][0]
        assert b'simple.file' in cmd
        assert b"'simple folder'" in cmd
        assert b"'special * folder'" in cmd
        assert b'not found * folder' in cmd
        assert rb'test\ \*\ folder/*.pattern' in cmd
        assert b"'!"  #$%&' "'" '()*+,-.012:;<=>?@ABC[\]^_`abc{|}~'" in cmd

    @patch('dups.rsync.rsync._exec')
    def test_excludes(self, mock_exec):
        sync = rsync.rsync()
        sync.sync(rsync.Path(context.TARGET_DIR), ['/'], [
            '/tmp',
            'simple folder',
            '*.mkv',
        ])

        cmd = mock_exec.call_args[0][0]
        assert b"--exclude /tmp" in cmd
        assert b"--exclude 'simple folder'" in cmd
        assert b"--exclude '*.mkv'" in cmd

    @patch('dups.rsync.rsync._exec')
    def test_link_dest(self, mock_exec):
        sync = rsync.rsync()
        sync.sync(rsync.Path('/'), [],
                  link_dest='/special * path/previous_backup')

        cmd = mock_exec.call_args[0][0]
        assert b'--delete' in cmd
        assert b"--link-dest '/special * path/previous_backup'" in cmd

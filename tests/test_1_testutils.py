import context  # noqa: F401, isort:skip
import os
import shutil

import testutils

STRUCT = {
    'dir1': {
        'sub1': {
            'file1': None
        }
    },
    '***dir2***': {
        '😀': None
    },
}


def teardown_function(func):
    if os.path.exists(context.TMP_DIR):
        shutil.rmtree(context.TMP_DIR)


def test_create_dir_struct():
    assert not os.path.isfile(
        os.path.join(context.TMP_DIR, 'dir1', 'sub1', 'file1'))
    assert not os.path.isfile(os.path.join(context.TMP_DIR, '***dir2***', '😀'))

    testutils.create_dir_struct(STRUCT, context.TMP_DIR)

    assert os.path.isfile(
        os.path.join(context.TMP_DIR, 'dir1', 'sub1', 'file1'))
    assert os.path.isfile(os.path.join(context.TMP_DIR, '***dir2***', '😀'))


def test_get_dir_struct():
    testutils.create_dir_struct(STRUCT, context.TMP_DIR)
    assert STRUCT == testutils.get_dir_struct(context.TMP_DIR)

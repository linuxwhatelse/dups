import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, os.path.abspath(os.path.join(HERE, os.pardir)))

BACKUP_DIR = os.path.join(HERE, 'backups')

DATA_DIR = os.path.join(HERE, 'data')

TEST_DIR = os.path.join(DATA_DIR, 'test.dir')
TEST_FILE = os.path.join(DATA_DIR, 'test.file')

SPECIAL_NAME = 'special ^°!"§$%&()=?´`+~#\',.-<>| \ \\\\ \\\\\\ \\\\\\\\'
SPECIAL_FILE = os.path.join(DATA_DIR, SPECIAL_NAME)

TMP_DIR = os.path.join(HERE, 'tmp.dir')
TMP_FILE = os.path.join(HERE, 'tmp.file')

SSH_HOST = 'localhost'
SSH_CONFIG = os.path.expanduser('~/.ssh/config')
SSH_CONFIG_INVALID = os.path.expanduser('~/.ssh/config_invalid')

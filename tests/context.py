import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, os.path.abspath(os.path.join(HERE, os.pardir)))

TMP_DIR = os.path.join(HERE, 'tmp')
TARGET_DIR = os.path.join(HERE, 'target')

# Deprecated stuff
BACKUP_DIR = os.path.join(HERE, 'backups')

DATA_DIR = os.path.join(HERE, 'data')

TEST_DIR = os.path.join(DATA_DIR, 'test.dir')
TEST_FILE = os.path.join(DATA_DIR, 'test.file')

TMP_FILE = os.path.join(HERE, 'tmp.file')

SSH_HOST = 'localhost'
SSH_CONFIG = os.path.expanduser('~/.ssh/config')
SSH_CONFIG_INVALID = os.path.expanduser('~/.ssh/config_invalid')

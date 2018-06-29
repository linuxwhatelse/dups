import getpass
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, os.path.abspath(os.path.join(HERE, os.pardir)))

BACKUP_DIR = os.path.join(HERE, 'backups')

DATA_DIR = os.path.join(HERE, 'data')

TEST_DIR = os.path.join(HERE, 'data', 'test.dir')
TEST_FILE = os.path.join(HERE, 'data', 'test.file')

TMP_DIR = os.path.join(HERE, 'tmp.dir')
TMP_FILE = os.path.join(HERE, 'tmp.file')

SSH_HOST = 'localhost'
SSH_PORT = 22
SSH_USER = getpass.getuser()
SSH_CONFIG = os.path.expanduser('~/.ssh/config')
SSH_KEY = os.path.expanduser('~/.ssh/id_rsa')

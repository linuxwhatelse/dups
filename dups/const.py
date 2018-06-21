"""
Constant variables used throught the application.

Attributes:
    HERE (str): Absolute path to the source directory of dups.
    APP_NAME (str): Name of the application.
    CONFIG_PATH (str): Absolute path to the users config file.
    CONFIG_TEMPLATE_PATH (str): Absolute path to the template config file.
    CACHE_DIR (str): Absolute path to the cache directory.
    DEFAULT_RESTORE_PATH (str): Path to the default restore directory.
    DBUS_NAME (str): Name used to register with dbus.
    DBUS_PATH (str): Path used to register with dbus.
"""
import os

HERE = os.path.dirname(os.path.realpath(__file__))

APP_NAME = 'dups'

CONFIG_PATH = os.path.expanduser('~/.config/dups.yaml')
CONFIG_TEMPLATE_PATH = os.path.join(HERE, 'data', 'config.yaml')

CACHE_DIR = os.path.expanduser('~/.cache/dups')
os.makedirs(CACHE_DIR, exist_ok=True)

DEFAULT_RESTORE_PATH = '/'

DBUS_NAME = 'de.linuxwhatelse.dups'
DBUS_PATH = '/de/linuxwhatelse/dups'

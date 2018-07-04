"""
Constant variables used throught the application.

Attributes:
    HERE (str): Absolute path to the source directory of dups.

    APP_NAME (str): Name of the application.
    APP_ICON (str): Name of the applications icon.

    CONFIG_PATH (str): Absolute path to the users config file.
    CONFIG_TEMPLATE_PATH (str): Absolute path to the template config file.

    CACHE_DIR (str): Absolute path to the cache directory.
    ENV_PATH (str): Absolute path to the environment file within CACHE_DIR.

    DEFAULT_RESTORE_PATH (str): Path to the default restore directory.

    DBUS_NAME (str): Name used to register with dbus.
    DBUS_PATH (str): Path used to register with dbus.
"""
import os

HERE = os.path.dirname(os.path.realpath(__file__))

APP_NAME = 'dups'
APP_ICON = 'security-high'  # Until we have our own icon

CONFIG_DIR = os.path.expanduser('~/.config/dups')
CONFIG_TEMPLATE_PATH = os.path.join(HERE, 'data', 'config.yaml')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.yaml')

CACHE_DIR = os.path.expanduser('~/.cache/dups')
ENV_PATH = os.path.join(CACHE_DIR, 'env.json')
os.makedirs(CACHE_DIR, exist_ok=True)

DEFAULT_RESTORE_PATH = '/'

DBUS_NAME = 'de.linuxwhatelse.dups'
DBUS_PATH = '/de/linuxwhatelse/dups'

import os
import threading
from typing import TypeVar

import ruamel.yaml

from . import const, utils

_CONFIG = TypeVar('_CONFIG', bound='Config')


class Config:
    """Class to represent dups config."""

    __instance = None
    __lock = threading.RLock()

    _config_file = None
    _config_template = None

    _user = None
    _template = None
    _combined = None

    def __init__(self):
        """Create a new config instance.
           Using `Config.get`_ is the preferred way."""
        self._config_template = const.CONFIG_TEMPLATE_FILE

        self._template = {}
        with open(self._config_template, 'r') as f:
            self._template = ruamel.yaml.YAML(typ='safe').load(f.read())

    @classmethod
    def get(cls) -> _CONFIG:
        """Get a instance of `Config`_.

        Returns:
            Config: A existing (or new if it's the first call)
                instance of `Config`_
        """
        if not cls.__instance:
            cls.__instance = cls()
        return cls.__instance

    def reload(self):
        """Reload the config data from file."""
        with Config.__lock:
            self._user = {}
            with open(self._config_file, 'r') as f:
                self._user = ruamel.yaml.YAML(typ='safe').load(f.read())

            self._combined = utils.dict_merge(self._template, self._user)

    def save(self):
        """Save the current configuration to file."""
        with Config.__lock:
            yaml = ruamel.yaml.YAML()
            yaml.indent(mapping=2, sequence=4, offset=2)

            with open(self._config_file, 'w+') as f:
                yaml.dump(self._user, f)

    @property
    def config_file(self):
        return self._config_file

    @config_file.setter
    def config_file(self, config_file):
        self._config_file = config_file
        self.reload()

    @property
    def config_template(self):
        return self._config_template

    @config_template.setter
    def config_template(self, template_file):
        self._config_template = template_file
        self.reload()

    def _add_list_data(self, key, values):
        """Add the given values to the list identified by the given key.

        Args:
            key (str): Name of the list to add all values to.
            values (list): Items to add to the given list.
        """
        self._user.setdefault(key, {})

        for val in values:
            if os.path.isdir(val):
                val = os.path.abspath(val)
                type_ = 'folders'
            elif os.path.isfile(val):
                val = os.path.abspath(val)
                type_ = 'files'
            else:
                type_ = 'patterns'

            self._user[key].setdefault(type_, []).append(val)
            self._user[key][type_].sort()

        self._combined = utils.dict_merge(self._template, self._user)

    def _remove_list_data(self, key, values):
        """Remove the given values from the list identified by the given key.

        Args:
            key (str): Name of the list to remove all values from.
            values (list): Items to remove from the given list.
        """
        if not isinstance(self._user.get(key, None), dict):
            return None

        for val in values:
            if os.path.isfile(val) or os.path.isdir(val):
                val = os.path.abspath(val)

            for type_ in ['folders', 'files', 'patterns']:
                if val in self._user[key].get(type_, []):
                    self._user[key][type_].remove(val)

        self._combined = utils.dict_merge(self._template, self._user)

    @property
    def target(self):
        """dict: The configured target with expanded paths."""
        t = self._combined['target']

        if t['path']:
            t['path'] = os.path.expanduser(t['path'])

        if t['ssh_config_file']:
            t['ssh_config_file'] = os.path.expanduser(t['ssh_config_file'])

        return t

    def get_includes(self, flat=False):
        """Get all configured includes.

        Args:
            flat (bool): Whether or not to merge folders, files and patterns
                into a flat list.

        Returns:
            dict|list: A `dict` if `flat` is `False`, a `list` otherwise.
        """
        if flat:
            incl = self._combined['includes']
            return [*incl['folders'], *incl['files'], *incl['patterns']]
        return self._combined['includes']

    def add_includes(self, values):
        """Add new items to the list of includes.

        Args:
            values (list): Files, folders and/or patterns to add to the list
                of includes.
        """
        self._add_list_data('includes', values)
        self.save()

    def remove_includes(self, values):
        """Remove the given items from the list of includes.

        Args:
            values (list): Files, folders and/or patterns to remove from the
                list of includes.
        """
        self._remove_list_data('includes', values)
        self.save()

    def get_excludes(self, flat=False):
        """Get all configured excludes.

        Args:
            flat (bool): Whether or not to merge folders, files and patterns
                into a flat list.

        Returns:
            dict|list: A `dict` if `flat` is `False`, a `list` otherwise.
        """
        if flat:
            excl = self._combined['excludes']
            return [*excl['folders'], *excl['files'], *excl['patterns']]
        return self._combined['excludes']

    def add_excludes(self, values):
        """Add new items to the list of excludes.

        Args:
            values (list): Files, folders and/or patterns to add to the list
                of excludes.
        """
        self._add_list_data('excludes', values)
        self.save()

    def remove_excludes(self, values):
        """Remove the given items from the list of excludes.

        Args:
            values (list): Files, folders and/or patterns to remove from the
                list of excludes.
        """
        self._remove_list_data('excludes', values)
        self.save()

    @property
    def notify(self):
        """bool: The configured notify state."""
        return self._combined['notify']

    @property
    def rsync(self):
        """dict: The configured rsync options."""
        return self._combined['rsync']

    @property
    def logging(self):
        """dict: The configured logging options."""
        return self._combined['logging']

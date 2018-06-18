import os

import ruamel.yaml

from . import utils


HERE = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.expanduser('~/.config/dups.yaml')


class Config:
    __instance = None
    _data = None

    def __init__(self):
        self._reload()

    @classmethod
    def get(cls):
        if not cls.__instance:
            cls.__instance = cls()
        return cls.__instance

    def _reload(self):
        config_data = dict()
        if os.path.isfile(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                config_data = ruamel.yaml.YAML(typ='safe').load(f.read())
        else:
            dir_ = os.path.dirname(CONFIG_PATH)
            if not os.path.exists(dir_):
                os.makedirs(dir_)
            return

        template = os.path.join(HERE, os.pardir, 'config.yaml')
        template_data = dict()
        with open(template, 'r') as f:
            template_data = ruamel.yaml.YAML(typ='safe').load(f.read())

        self._data = utils.dict_merge(template_data, config_data)

    def _save(self):
        yaml = ruamel.yaml.YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)

        with open(CONFIG_PATH, 'w+') as f:
            yaml.dump(self._data, f)

    def _add_list_data(self, key, values):
        if not isinstance(self._data[key], list):
            self._data[key] = list()

        new_values = list()
        for val in values:
            if os.path.isfile(val) or os.path.isdir(val):
                val = os.path.abspath(val)
            new_values.append(val)

        self._data[key].extend(new_values)
        self._data[key] = sorted(list(set(self._data[key])))

    def _remove_list_data(self, key, values):
        if not isinstance(self._data[key], list):
            return None

        for val in values:
            if os.path.isfile(val) or os.path.isdir(val):
                val = os.path.abspath(val)
            self._data[key].remove(val)

    @property
    def target(self):
        t = self._data['target']

        if t['path']:
            t['path'] = os.path.expanduser(t['path'])

        if t['ssh_key_file']:
            t['ssh_key_file'] = os.path.expanduser(t['ssh_key_file'])

        return t

    @property
    def includes(self):
        return self._data['includes']

    def add_includes(self, values):
        self._add_list_data('includes', values)
        self._save()

    def remove_includes(self, values):
        self._remove_list_data('includes', values)
        self._save()

    @property
    def excludes(self):
        return self._data['excludes']

    def add_excludes(self, values):
        self._add_list_data('excludes', values)
        self._save()

    def remove_excludes(self, values):
        self._remove_list_data('excludes', values)
        self._save()

    @property
    def logging(self):
        return self._data['logging']

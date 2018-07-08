import os

from setuptools import find_packages, setup

HERE = os.path.dirname(os.path.realpath(__file__))


def get_requirements():
    requirements = []
    with open(os.path.join(HERE, 'requirements.txt'), 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                if line.lstrip('#').strip().lower().startswith('unittests'):
                    break
                continue
            requirements.append(line)

    return requirements


def get_data_files():
    include_data_files = os.environ.get('INCLUDE_DATA_FILES', '').split(' ')
    include_data_files = [i.strip().lower() for i in include_data_files]

    data_files = []
    if 'systemd' in include_data_files:
        data_files.append(('/usr/lib/systemd/user/',
                           ['data/usr/lib/systemd/user/dups.service']))
        data_files.append(('/usr/lib/systemd/system/',
                           ['data/usr/lib/systemd/system/dups@.service']))

    if 'dbus' in include_data_files:
        data_files.append(
            ('/etc/dbus-1/system.d/',
             ['data/etc/dbus-1/system.d/de.linuxwhatelse.dups.conf']))

    return data_files


setup(
    name='dups',
    version='0.0.0',
    description='It deduplicates things - Backup as simple as possible.',
    long_description='',
    url='http://linuxwhatelse.de',
    author='linuxwhatelse',
    author_email='info@linuxwhatelse.de',
    license='GPLv3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3 :: Only',
    ],
    python_requires='~=3.5',
    packages=find_packages(),
    package_data={'dups': [
        'data/config.yaml',
    ]},
    data_files=get_data_files(),
    scripts=['bin/dups'],
    install_requires=get_requirements(),
    zip_safe=False,
)

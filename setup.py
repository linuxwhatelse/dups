import os

from setuptools import find_packages, setup


def get_data_files():
    include_data_files = os.environ.get('INCLUDE_DATA_FILES', '').split(' ')
    include_data_files = [i.strip().lower() for i in include_data_files]

    data_files = []
    if 'systemd' in include_data_files:
        data_files.extend((
            ('/usr/lib/systemd/user/',
             ['data/usr/lib/systemd/user/dups.service']),
            ('/usr/lib/systemd/system/',
             ['data/usr/lib/systemd/system/dups@.service']),
        ))

    if 'dbus' in include_data_files:
        data_files.append(
            ('/etc/dbus-1/system.d/',
             ['data/etc/dbus-1/system.d/de.linuxwhatelse.dups.daemon.conf']))

    if 'desktop' in include_data_files:
        data_files.extend((
            ('/usr/share/applications/',
             ['data/usr/share/applications/de.linuxwhatelse.dups.desktop']),
            ('/usr/share/icons/hicolor/48x48/apps/',
             ['data/usr/share/icons/hicolor/48x48/apps/dups.png']),
            ('/usr/share/icons/hicolor/512x512/apps/',
             ['data/usr/share/icons/hicolor/512x512/apps/dups.png']),
            ('/usr/share/icons/hicolor/scalable/apps/',
             ['data/usr/share/icons/hicolor/scalable/apps/dups.svg']),
        ))

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
        'data/ssh',
    ]},
    data_files=get_data_files(),
    scripts=['data/bin/dups'],
    install_requires=['paramiko', 'ruamel.yaml>=0.15.0'],
    extras_require={
        'daemon': ['dbus-python'],
        'notification': ['pygobject']
    },
    zip_safe=False,
)

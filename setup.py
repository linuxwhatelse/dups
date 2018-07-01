import os

from setuptools import find_packages, setup

HERE = os.path.dirname(os.path.realpath(__file__))
DATA_FILES = list()

INCLUDE_DATA_FILES = os.environ.get('INCLUDE_DATA_FILES', 'False') == 'True'


def get_requirements():
    requirements = list()
    with open(os.path.join(HERE, 'requirements.txt'), 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                if line.lstrip('#').strip().lower().startswith('unittests'):
                    break
                continue
            requirements.append(line)

    return requirements


if INCLUDE_DATA_FILES:
    DATA_FILES.append(('/usr/lib/systemd/user', ['data/systemd/dups.service']))

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
    data_files=DATA_FILES,
    scripts=['bin/dups'],
    install_requires=get_requirements(),
    zip_safe=False,
)

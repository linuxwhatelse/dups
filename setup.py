import os

from setuptools import find_packages, setup

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def get_requirements():
    requirements = list()
    with open('requirements.txt', 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            requirements.append(line)

    return requirements


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
    include_package_data=True,  # Reads from MANIFEST.in
    scripts=['bin/dups'],
    install_requires=get_requirements(),
    zip_safe=False,
    data_files=[
        ('/usr/lib/systemd/user', ['data/systemd/dups.service']),
    ])

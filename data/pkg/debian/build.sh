#!/usr/bin/env bash

# Navigate to the project root
cd "$(realpath "$(dirname "$0")/../../../")"
python3 setup.py --command-packages=stdeb.command bdist_deb

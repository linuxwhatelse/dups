#!/usr/bin/env bash

cd "$(dirname "$0")"

pacman --noconfirm -U *.pkg.tar.xz

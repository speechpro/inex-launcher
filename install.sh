#!/bin/bash

if [ ! -d venv ]; then
  python3 -m venv venv || exit 1
fi

source venv/bin/activate || exit 1

./inst-dep.sh || exit 1

pip install -e . || exit 1

pytest || exit 1

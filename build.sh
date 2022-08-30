#!/bin/bash

./test.sh || exit 1

python setup.py sdist || exit 1
python setup.py bdist_wheel || exit 1

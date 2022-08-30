#!/bin/bash

#./test.sh || exit 1

python setup.py sdist upload \
  -r https://nid-artifactory.ad.speechpro.com/artifactory/api/pypi/pypi || exit 1

python setup.py bdist_wheel upload \
  -r https://nid-artifactory.ad.speechpro.com/artifactory/api/pypi/pypi || exit 1

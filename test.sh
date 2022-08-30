#!/bin/bash

#./inst-dep.sh || exit 1

tox -e test || exit 1

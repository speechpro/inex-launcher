#!/bin/bash

for dir in build dist mkernel.egg-info .eggs .pytest_cache .tox; do
  [ -d $dir ] && rm -r $dir
done
rm -rf mkernel.*.so 2> /dev/null

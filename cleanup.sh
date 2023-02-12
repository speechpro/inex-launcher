#!/bin/bash

for dir in build dist inex.egg-info .eggs .pytest_cache .tox; do
  [ -d $dir ] && rm -r $dir
done
rm -rf inex.*.so 2> /dev/null

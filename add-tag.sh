#!/bin/bash

tag=v$(cat inex/version.txt)
mark=$(git tag | grep $tag)
if [ -z "$mark" ]; then
  echo "Creating new tag $tag"
  git tag $tag
  echo Done
else
  echo "Tag $tag already exists"
fi

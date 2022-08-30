#!/bin/bash

pip install -U pip || exit 1
pip install -r build-deps.txt || exit 1
pip install -r requirements.txt || exit 1

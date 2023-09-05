#!/bin/bash

source ~/.pyenv/versions/educanoferta/bin/activate
cd "$(dirname "$0")"
exec python main.py run

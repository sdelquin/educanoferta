#!/bin/bash

source ~/.pyenv/versions/nombrame/bin/activate
cd "$(dirname "$0")"
exec python main.py run

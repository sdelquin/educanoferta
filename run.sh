#!/bin/bash

cd "$(dirname "$0")"
source .venv/bin/activate
exec python main.py run

#!/usr/bin/env bash

set -e

set -a
source .env
set +a

#export MIDP_LOG_LEVEL=debug
python3 -m unittest $@

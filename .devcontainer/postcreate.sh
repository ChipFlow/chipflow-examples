#!/usr/bin/env bash
set -ex
curl -sSL https://pdm-project.org/install-pdm.py | python3 -
pdm lock -d
pdm install

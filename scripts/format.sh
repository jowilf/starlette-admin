#!/usr/bin/env bash

set -e
set -x
ruff starlette_admin tests --fix
black .

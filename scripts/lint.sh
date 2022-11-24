#!/usr/bin/env bash

set -e
set -x

mypy starlette_admin
ruff starlette_admin tests
black starlette_admin tests --check
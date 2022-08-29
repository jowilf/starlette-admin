#!/usr/bin/env bash

set -e
set -x

mypy starlette_admin
flake8 starlette_admin tests
black starlette_admin tests  --check
isort starlette_admin tests  --check-only
#!/bin/sh

# to use: ./i18n/init.sh fr
pybabel init -i i18n/admin.pot -d starlette_admin/translations -D admin -l $1

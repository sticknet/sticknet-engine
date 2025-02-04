#!/bin/bash
set -e

# --------------------------------------------
# 1. Install PostgreSQL system packages
# --------------------------------------------
# These libraries (for example, postgresql-devel)
# are required so that Python modules like psycopg2
# can compile correctly.
yum install -y postgresql postgresql-devel

# --------------------------------------------
# 2. Activate the virtual environment
# --------------------------------------------
# Elastic Beanstalk creates a virtual environment
# for your Python application. The virtualenv is
# located under /var/app/venv/ and the activated
# environment will be used for the pip install below.
source /var/app/venv/*/bin/activate

# --------------------------------------------
# 3. Install Python packages
# --------------------------------------------
# You can install packages in one (or both) of two ways:
#
# (a) List packages here to install via pip. For example:
#
#     pip install Django psycopg2-binary
#
# (b) If you have a requirements.txt file in your project
#     (recommended), install it as well.
#
# In this example, we install Django (and psycopg2-binary
# so that Django can talk to PostgreSQL) and then, if present,
# install any additional packages from requirements.txt.
pip install Django psycopg2-binary

if [ -f /var/app/current/requirements.txt ]; then
    pip install -r /var/app/current/requirements.txt
fi

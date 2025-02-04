#!/bin/bash
set -e

# --------------------------------------------
# 1. Install PostgreSQL system packages (for AL2023)
# --------------------------------------------
# On Amazon Linux 2023, install the PostgreSQL client
# and the development headers from libpq-devel.
yum install -y libpq-devel libmemcached-devel zlib-devel

# --------------------------------------------
# 2. Activate the virtual environment
# --------------------------------------------
# Elastic Beanstalk creates a virtual environment for your Python application.
# The virtualenv is located under /var/app/venv/ and the activated environment
# will be used for the pip install below.
source /var/app/venv/*/bin/activate

# --------------------------------------------
# 3. Install Python packages
# --------------------------------------------
# You can install packages directly here via pip or install from requirements.txt.
# Here we install Django and psycopg2-binary (which uses the libpq headers above).
pip install --upgrade pip setuptools wheel
pip install setuptools==67.6.0

# If a requirements.txt file exists, install any additional packages.
if [ -f /var/app/current/requirements.txt ]; then
    pip install -r /var/app/current/requirements.txt
fi

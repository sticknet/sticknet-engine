#!/bin/bash
set -e

# --------------------------------------------
# 1. Install PostgreSQL system packages (versioned)
# --------------------------------------------
# For Amazon Linux 2023, install the versioned PostgreSQL packages.
yum install -y postgresql15 postgresql15-devel

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

if [ -f /var/app/current/requirements.txt ]; then
    pip install -r /var/app/current/requirements.txt
fi

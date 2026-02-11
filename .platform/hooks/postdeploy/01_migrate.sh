#!/bin/bash
set -e

# Run this command only on the leader instance.
#if [ "$EB_IS_COMMAND_LEADER" != "true" ]; then
#  echo "This instance is not the leader. Skipping database migrations."
#  exit 0
#fi

echo "Activating virtual environment and running migrations..."
source /var/app/venv/*/bin/activate
python3 /var/app/current/src/manage.py migrate --noinput
python3 /var/app/current/src/manage.py collectstatic --noinput

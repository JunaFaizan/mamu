#!/bin/bash
set -o errexit

pip install --break-system-packages -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

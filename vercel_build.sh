#!/bin/bash
pip install --upgrade pip
pip install psycopg2-binary
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

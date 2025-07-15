#!/usr/bin/env bash
# start.sh
gunicorn --bind 0.0.0.0:$PORT main:app

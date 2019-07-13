#!/usr/bin/env bash
source ./venv/bin/activate
python3 epg-filter.py
cp -v /tmp/epg-all.xml /srv/dev-disk-by-label-media/epg
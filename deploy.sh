#!/bin/bash
set -eu

echo "Fetching origin repository"
git fetch --all
git reset --mixed origin/master

dt=`date '+%Y-%m-%dT%H-%M-%S'`
echo "Making database and logs backup ${dt}.tar.xz"
tar -cJvf "../backup/${dt}.tar.xz" database logging.log

echo "Installing Python dependencies"
mkdir -p database
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt > /dev/null
echo "Installed Python dependencies"

echo "Installing systemd service"
repo_dir="$(dirname "$0")"
sudo chown -R melo:melo "$repo_dir"
sudo install -m644 rustbot.service /usr/local/lib/systemd/system/rustbot.service
sudo chown root:root /usr/local/lib/systemd/system/rustbot.service
echo "Installed systemd service"

echo "Starting rustbot systemd service"
sudo systemctl daemon-reload
sudo systemctl restart rustbot.service
echo "Started rustbot systemd service"

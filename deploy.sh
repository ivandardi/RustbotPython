#!/bin/bash
set -eu

git fetch --all
git reset --mixed origin/master

repo_dir="$(dirname "$0")"

mkdir -p database
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt > /dev/null
echo "Installed Python dependencies"

sudo chown -R melo:melo "$repo_dir"
sudo install -m644 rustbot.service /usr/local/lib/systemd/system/rustbot.service
sudo chown root:root /usr/local/lib/systemd/system/rustbot.service
echo "Installed systemd service"

sudo systemctl daemon-reload
sudo systemctl restart rustbot.service
echo "Started rustbot systemd service"

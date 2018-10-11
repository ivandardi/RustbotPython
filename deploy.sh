#!/bin/bash
set -eu

git fetch --all
git reset --hard origin/master

repo_dir="$(dirname "$0")"
dest_dir=/home/melo/prod

sudo rm -rf "$dest_dir"
mkdir -p "$dest_dir"
cp -a "$repo_dir" "$dest_dir"
echo "Installed source code to '$dest_dir'"

cd "$dest_dir"
python3.6 -m venv venv > /dev/null
source venv/bin/activate > /dev/null
pip install -r requirements.txt > /dev/null
echo "Installed Python dependencies"

sudo chown -R melo:melo "$dest_dir"
sudo install -m644 rustbot.service /usr/local/lib/systemd/system/rustbot.service
sudo chown root:root /usr/local/lib/systemd/system/rustbot.service
echo "Installed systemd service"

sudo systemctl daemon-reload
sudo systemctl restart rustbot.service
echo "Started rustbot systemd service"

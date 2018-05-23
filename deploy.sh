#!/bin/bash
set -eu

repo_dir="$(dirname "$0")"
dest_dir=/home/ferris/prod

rm -r "$dest_dir"
mkdir -p "$dest_dir"
cp -a "$repo_dir" "$dest_dir"
chown -R ferris:ferris "$dest_dir"
echo "Installed source code to '$dest_dir'"

pipenv install > /dev/null
echo "Installed Python dependencies"

install -m644 "$repo_dir/rustbot.service" /usr/local/lib/systemd/system/rustbot.service
chown root:root /usr/local/lib/systemd/system/rustbot.service
echo "Installed systemd service"

systemctl daemon-reload
systemctl restart rustbot.service
echo "Started rustbot systemd service"

#!/usr/bin/env bash
set -euo pipefail

# Link host git config(s) into /root
mkdir -p /root /root/.config/git

FOUND=0
if [ -f /host-home/.gitconfig ]; then
	ln -sf /host-home/.gitconfig /root/.gitconfig
	FOUND=1
fi

if [ -f /host-home/.config/git/config ]; then
	ln -sf /host-home/.config/git/config /root/.config/git/config
	FOUND=1
fi

# Optional: global ignore
if [ -f /host-home/.gitignore_global ]; then
	ln -sf /host-home/.gitignore_global /root/.gitignore_global
fi

# Make repo safe for root
git config --global --add safe.directory /workspace || true

if [ "$FOUND" -eq 0 ]; then
	echo "[devcontainer] No host git config found. Configure git on your HOST:"
	echo "  git config --global user.name 'Your Name'"
	echo "  git config --global user.email 'you@example.com'"
fi

# Sanity note about read-only SSH mount
if [ ! -w /root/.ssh ]; then
	echo "[devcontainer] Mounted /root/.ssh is read-only. If you need to add to known_hosts from inside the container,"
	echo "               change the mount to remove ',readonly' in devcontainer.json."
fi

#!/bin/bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="$(id -un)"
sudo apt update
sudo apt install -y chromium unclutter
sudo cp "$APP_DIR/systemd/mi-inspire.service" /etc/systemd/system/mi-inspire.service
sudo sed -i "s|__APP_DIR__|$APP_DIR|g; s|__USER__|$USER_NAME|g" /etc/systemd/system/mi-inspire.service
sudo systemctl daemon-reload
sudo systemctl enable --now mi-inspire.service
mkdir -p "$HOME/.config/autostart"
sed "s|__APP_DIR__|$APP_DIR|g" "$APP_DIR/systemd/mi-inspire-kiosk.desktop" > "$HOME/.config/autostart/mi-inspire-kiosk.desktop"
echo "Installazione completata. Regia: http://$(hostname -I | awk '{print $1}'):8080"
echo "Riavvia il Raspberry con: sudo reboot"

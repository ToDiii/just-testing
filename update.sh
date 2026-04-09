#!/usr/bin/env bash

# This script updates the 'just-testing' application.
# It pulls the latest changes from the repository and rebuilds everything.

YW="\033[33m"
BL="\033[36m"
RD="\033[01;31m"
GN="\033[1;92m"
CE="\033[0m"

function msg_info() {
    echo -e "${BL}[INFO] $1${CE}"
}

function msg_ok() {
    echo -e "${GN}[OK] $1${CE}"
}

function msg_error() {
    echo -e "${RD}[ERROR] $1${CE}"
    exit 1
}

if [[ $(id -u) -ne 0 ]]; then
    msg_error "This script must be run as root."
fi

msg_info "Starting update for 'just-testing'..."

cd /opt/just-testing || msg_error "Directory /opt/just-testing not found."

msg_info "Pulling latest changes from Git..."
git pull origin main || msg_error "Failed to pull from git."
msg_ok "Git pull successful."

msg_info "Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt &>/dev/null || msg_error "Failed to pip install requirements."
deactivate
msg_ok "Python dependencies updated."

msg_info "Updating Node.js dependencies and rebuilding frontend..."
npm install --legacy-peer-deps &>/dev/null || msg_error "Failed to install node modules."
npm run build &>/dev/null || msg_error "Failed to build the frontend."
msg_ok "Frontend rebuilt successfully."

msg_info "Restoring permissions..."
chown -R just-testing:just-testing /opt/just-testing
msg_ok "Permissions restored."

msg_info "Restarting just-testing service..."
systemctl restart just-testing || msg_error "Failed to restart the service."
msg_ok "Service restarted successfully."

echo -e "\n${GN}Update Complete!${CE}\n"

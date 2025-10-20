#!/usr/bin/env bash

# This script installs the 'just-testing' application in a Proxmox LXC container.
# It is designed to be run on a Debian or Ubuntu based container.

YW=$(echo "\033[33m")
BL=$(echo "\033[36m")
RD=$(echo "\033[01;31m")
BGN=$(echo "\033[4;92m")
GN=$(echo "\033[1;92m")
CE=$(echo "\033[0m")

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

# --- Check for root privileges ---
if [[ $(id -u) -ne 0 ]]; then
    msg_error "This script must be run as root."
fi

msg_info "Starting installation of 'just-testing' application..."

# --- 1. Update System and Install Dependencies ---
msg_info "Updating package lists and installing system dependencies..."
export DEBIAN_FRONTEND=noninteractive
apt-get update &>/dev/null
apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev &>/dev/null

msg_info "Installing Node.js v18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash - &>/dev/null
apt-get install -y nodejs &>/dev/null
msg_ok "System dependencies installed."

# --- 2. Clone Repository ---
msg_info "Cloning 'just-testing' repository from GitHub..."
if [ -d "/opt/just-testing" ]; then
    rm -rf /opt/just-testing
fi
git clone https://github.com/ToDiii/just-testing.git /opt/just-testing &>/dev/null
msg_ok "Repository cloned to /opt/just-testing."

# --- 3. Set up Python Backend ---
msg_info "Setting up Python virtual environment and installing dependencies..."
cd /opt/just-testing
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt &>/dev/null
deactivate
msg_ok "Python backend setup complete."

# --- 4. Set up Node.js Frontend ---
msg_info "Installing Node.js dependencies and building frontend..."
npm install --legacy-peer-deps &>/dev/null
npm run build &>/dev/null
msg_ok "Node.js frontend setup complete."

# --- 5. Create Service User and Set Permissions ---
msg_info "Creating service user 'just-testing'..."
useradd -r -s /bin/false just-testing
chown -R just-testing:just-testing /opt/just-testing
msg_ok "Service user created and permissions set."

# --- 6. Create systemd Service ---
msg_info "Creating systemd service file..."
cat << EOF > /etc/systemd/system/just-testing.service
[Unit]
Description=Just Testing Application Service
After=network.target

[Service]
User=just-testing
Group=just-testing
WorkingDirectory=/opt/just-testing
ExecStart=/opt/just-testing/venv/bin/uvicorn webapp.main:app --host 0.0.0.0 --port 8000
Restart=always

# IMPORTANT: Set a secure API key for production use.
Environment="API_KEY=dev"

[Install]
WantedBy=multi-user.target
EOF
msg_ok "Systemd service file created."

# --- 7. Enable and Start Service ---
msg_info "Enabling and starting the 'just-testing' service..."
systemctl daemon-reload
systemctl enable --now just-testing.service &>/dev/null
msg_ok "Service enabled and started."

# --- 8. Final Message ---
IP=$(hostname -I | awk '{print $1}')
echo -e "\n${BGN}Installation Complete!${CE}\n"
echo -e "You can access the application at: ${GN}http://${IP}:8000${CE}"
echo -e "The application runs as a background service."
echo -e "${YW}For production, it is recommended to set a secure API_KEY in '/etc/systemd/system/just-testing.service' and restart the service.${CE}"
echo ""

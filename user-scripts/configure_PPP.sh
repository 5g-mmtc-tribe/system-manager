#!/bin/bash
# This script configures the PPP modem based on Data over UART with PPP User Guide Cloud Sequans.
# It creates or updates the following files:
#   - /etc/ppp/options
#   - /etc/chatscripts/connect
#   - /etc/chatscripts/disconnect
#
# Run this script as root.

# Ensure the script is executed as root.
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root."
  exit 1
fi

# Create /etc/ppp/options with the specified settings.
cat > /etc/ppp/options << 'EOF'
/dev/ttyUSB2
115200
nodetach
noauth
local
noipdefault
defaultroute
usepeerdns
crtscts
lock
debug
dump
-chap
connect "/usr/sbin/chat -t6 -f /etc/chatscripts/connect"
disconnect "/usr/sbin/chat -t6 -f /etc/chatscripts/disconnect"
EOF

# Create /etc/chatscripts/connect with the specified commands.
cat > /etc/chatscripts/connect << 'EOF'
#ABORT "NO CARRIER"
TIMEOUT 30
ABORT ERROR
"" AT
OK AT+CFUN=1
OK AT+CGDATA="PPP",1
CONNECT ""
EOF

# Create /etc/chatscripts/disconnect with the specified command.
cat > /etc/chatscripts/disconnect << 'EOF'
"" "\d\d\d+++\c"
EOF

echo "PPP modem configuration completed successfully."

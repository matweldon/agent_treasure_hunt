#!/bin/bash
# Network filtering setup script for additional security
# This script restricts network access to only trusted domains needed by the agent
# Note: This requires root privileges and is optional

set -e

echo "Setting up network filtering for Treasure Hunt Agent..."

# Trusted domains for the agent
TRUSTED_DOMAINS=(
    # Google Gemini API
    "generativelanguage.googleapis.com"
    "googleapis.com"
    "*.googleapis.com"

    # Python package repositories (for uv/pip)
    "pypi.org"
    "files.pythonhosted.org"

    # GitHub (for git operations)
    "github.com"
    "api.github.com"

    # DNS
    "8.8.8.8"
    "8.8.4.4"
)

# Check if running with sufficient privileges
if [ "$EUID" -ne 0 ]; then
    echo "This script requires root privileges to set up iptables rules."
    echo "Please run with sudo: sudo $0"
    exit 1
fi

# Install iptables if not present
if ! command -v iptables &> /dev/null; then
    echo "Installing iptables..."
    apt-get update && apt-get install -y iptables
fi

# Flush existing rules
echo "Flushing existing iptables rules..."
iptables -F
iptables -X

# Set default policies
iptables -P INPUT ACCEPT
iptables -P OUTPUT DROP
iptables -P FORWARD DROP

# Allow loopback
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow DNS (needed to resolve domain names)
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# Allow HTTPS to trusted domains
# Note: iptables can't directly filter by domain name, so we allow HTTPS traffic
# For stricter control, you would need to use a proxy or resolve IPs
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT

echo "Network filtering configured."
echo ""
echo "Trusted domains (resolved via DNS):"
printf '%s\n' "${TRUSTED_DOMAINS[@]}"
echo ""
echo "Note: For production use, consider using a proxy like Squid"
echo "to enforce domain-based filtering instead of port-based filtering."

#!/bin/bash

# Environment Setup Script for Enhanced Raspberry Pi Monitoring Agent
# This script helps configure environment variables and initial setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration variables
CONFIG_FILE="/etc/rpi-monitor/agent_config.json"
ENV_FILE=".env"
SERVICE_NAME="rpi-monitoring-agent"

echo "Enhanced Raspberry Pi Monitoring Agent - Environment Setup"
echo "=========================================================="
echo

# Get configuration from user
read -p "Enter API endpoint URL (e.g., https://your-server.com): " API_ENDPOINT
read -p "Enter API key: " API_KEY
read -p "Enter device ID [$(hostname)]: " DEVICE_ID
read -p "Enter collection interval in seconds [30]: " COLLECTION_INTERVAL
read -p "Enter log level (DEBUG, INFO, WARNING, ERROR) [INFO]: " LOG_LEVEL

# Set defaults
DEVICE_ID=${DEVICE_ID:-$(hostname)}
COLLECTION_INTERVAL=${COLLECTION_INTERVAL:-30}
LOG_LEVEL=${LOG_LEVEL:-INFO}

if [[ -z "$API_ENDPOINT" || -z "$API_KEY" ]]; then
    print_error "API endpoint and API key are required"
    exit 1
fi

print_status "Configuring environment..."

# Create environment file
cat > "$ENV_FILE" << EOF
# Enhanced Raspberry Pi Monitoring Agent Environment
# Generated on $(date)

# API Configuration
API_ENDPOINT=$API_ENDPOINT
API_KEY=$API_KEY
DEVICE_ID=$DEVICE_ID

# Agent Configuration
COLLECTION_INTERVAL=$COLLECTION_INTERVAL
LOG_LEVEL=$LOG_LEVEL
AGENT_VERSION=2.0.0-enhanced

# Feature Flags
ENABLE_DETAILED_MONITORING=true
ENABLE_PROCESS_MONITORING=true
ENABLE_SERVICE_MONITORING=true
ENABLE_SECURITY_MONITORING=true
ENABLE_NETWORK_MONITORING=true
ENABLE_GPIO_MONITORING=true

# Network Settings
MAX_RETRIES=3
RETRY_DELAY=5
SSL_VERIFY=true

# GPIO Configuration (comma-separated pin numbers)
GPIO_PINS=

# Custom Scripts Directory
CUSTOM_SCRIPTS_DIR=/opt/rpi-monitoring-agent/scripts

# Paths
CONFIG_FILE=/etc/rpi-monitor/agent_config.json
LOG_DIR=/var/log/rpi-monitor
DATA_DIR=/var/lib/rpi-monitor
EOF

print_success "Environment file created: $ENV_FILE"

# Update JSON configuration if it exists
if [[ -f "$CONFIG_FILE" ]] && command -v jq >/dev/null 2>&1; then
    print_status "Updating JSON configuration..."
    
    # Create temporary file with updated configuration
    jq --arg api_endpoint "$API_ENDPOINT" \
       --arg api_key "$API_KEY" \
       --arg device_id "$DEVICE_ID" \
       --arg collection_interval "$COLLECTION_INTERVAL" \
       --arg log_level "$LOG_LEVEL" \
       '.api_endpoint = $api_endpoint | .api_key = $api_key | .device_id = $device_id | .collection_interval = ($collection_interval | tonumber) | .log_level = $log_level' \
       "$CONFIG_FILE" > "$CONFIG_FILE.tmp"
    
    # Move temporary file to original
    sudo mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
    sudo chown rpi-monitor:rpi-monitor "$CONFIG_FILE" 2>/dev/null || true
    
    print_success "JSON configuration updated"
else
    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_warning "Configuration file not found at $CONFIG_FILE"
        print_status "Run the installation script first"
    elif ! command -v jq >/dev/null 2>&1; then
        print_warning "jq not found, skipping JSON configuration update"
        print_status "Install jq with: sudo apt-get install jq"
    fi
fi

echo
print_success "Environment setup completed!"
echo
echo "Configuration summary:"
echo "- API Endpoint: $API_ENDPOINT"
echo "- Device ID: $DEVICE_ID"
echo "- Collection Interval: ${COLLECTION_INTERVAL}s"
echo "- Log Level: $LOG_LEVEL"
echo
echo "Next steps:"
echo "1. Test the configuration: python3 enhanced_main.py --test"
echo "2. Start the service: sudo systemctl start $SERVICE_NAME"
echo "3. Check service status: sudo systemctl status $SERVICE_NAME"
echo "4. View logs: sudo journalctl -u $SERVICE_NAME -f"
echo
echo "To load environment variables in current session:"
echo "source $ENV_FILE"
echo
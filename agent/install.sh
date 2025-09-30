#!/bin/bash

# Enhanced Raspberry Pi Monitoring Agent Installation Script
# Adapted from Telegram monitoring system for API backend integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AGENT_USER="rpi-monitor"
AGENT_HOME="/opt/rpi-monitoring-agent"
SERVICE_NAME="rpi-monitoring-agent"
CONFIG_DIR="/etc/rpi-monitor"
LOG_DIR="/var/log/rpi-monitor"
DATA_DIR="/var/lib/rpi-monitor"

# Functions
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

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

check_raspberry_pi() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_warning "This doesn't appear to be a Raspberry Pi"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

install_dependencies() {
    print_status "Installing system dependencies..."
    
    # Update package lists
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        git \
        curl \
        systemd \
        rsyslog
    
    print_success "System dependencies installed"
}

create_user() {
    if ! id "$AGENT_USER" &>/dev/null; then
        print_status "Creating user $AGENT_USER..."
        useradd --system --home "$AGENT_HOME" --shell /bin/bash --create-home "$AGENT_USER"
        
        # Add user to gpio group for GPIO access
        if getent group gpio >/dev/null; then
            usermod -a -G gpio "$AGENT_USER"
        fi
        
        # Add user to i2c group for sensor access
        if getent group i2c >/dev/null; then
            usermod -a -G i2c "$AGENT_USER"
        fi
        
        print_success "User $AGENT_USER created"
    else
        print_status "User $AGENT_USER already exists"
    fi
}

create_directories() {
    print_status "Creating directories..."
    
    # Create directories
    mkdir -p "$AGENT_HOME"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$DATA_DIR/logs"
    mkdir -p "$DATA_DIR/metrics"
    mkdir -p "$DATA_DIR/backups"
    
    # Set ownership and permissions
    chown -R "$AGENT_USER:$AGENT_USER" "$AGENT_HOME"
    chown -R "$AGENT_USER:$AGENT_USER" "$CONFIG_DIR"
    chown -R "$AGENT_USER:$AGENT_USER" "$LOG_DIR"
    chown -R "$AGENT_USER:$AGENT_USER" "$DATA_DIR"
    
    chmod 755 "$AGENT_HOME"
    chmod 750 "$CONFIG_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "$DATA_DIR"
    
    print_success "Directories created"
}

install_agent() {
    print_status "Installing monitoring agent..."
    
    # Get script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    
    # Copy agent files
    cp -r "$SCRIPT_DIR"/* "$AGENT_HOME/"
    
    # Remove install script from agent directory
    rm -f "$AGENT_HOME/install.sh"
    
    # Set ownership
    chown -R "$AGENT_USER:$AGENT_USER" "$AGENT_HOME"
    
    # Make scripts executable
    chmod +x "$AGENT_HOME/enhanced_main.py"
    
    print_success "Agent files installed"
}

setup_python_environment() {
    print_status "Setting up Python virtual environment..."
    
    # Create virtual environment
    sudo -u "$AGENT_USER" python3 -m venv "$AGENT_HOME/venv"
    
    # Upgrade pip
    sudo -u "$AGENT_USER" "$AGENT_HOME/venv/bin/pip" install --upgrade pip
    
    # Install requirements
    if [[ -f "$AGENT_HOME/enhanced_requirements.txt" ]]; then
        sudo -u "$AGENT_USER" "$AGENT_HOME/venv/bin/pip" install -r "$AGENT_HOME/enhanced_requirements.txt"
    else
        print_error "Requirements file not found"
        exit 1
    fi
    
    print_success "Python environment set up"
}

create_systemd_service() {
    print_status "Creating systemd service..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Enhanced Raspberry Pi Monitoring Agent
After=network.target
Wants=network.target

[Service]
Type=simple
User=$AGENT_USER
Group=$AGENT_USER
WorkingDirectory=$AGENT_HOME
Environment=PATH=$AGENT_HOME/venv/bin
ExecStart=$AGENT_HOME/venv/bin/python $AGENT_HOME/enhanced_main.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=rpi-monitor

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$CONFIG_DIR $LOG_DIR $DATA_DIR

# Environment variables
Environment=CONFIG_FILE=$CONFIG_DIR/agent_config.json
Environment=LOG_LEVEL=INFO

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    print_success "Systemd service created"
}

setup_logrotate() {
    print_status "Setting up log rotation..."
    
    cat > /etc/logrotate.d/rpi-monitoring-agent << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $AGENT_USER $AGENT_USER
    postrotate
        systemctl reload $SERVICE_NAME 2>/dev/null || true
    endscript
}
EOF
    
    print_success "Log rotation configured"
}

configure_agent() {
    print_status "Creating default configuration..."
    
    # Create default config file
    cat > "$CONFIG_DIR/agent_config.json" << EOF
{
  "api_endpoint": "http://localhost:8000",
  "api_key": "your-api-key-here",
  "device_id": "$(hostname)",
  "collection_interval": 30,
  "log_level": "INFO",
  "enable_detailed_monitoring": true,
  "enable_process_monitoring": true,
  "enable_service_monitoring": true,
  "enable_security_monitoring": true,
  "enable_network_monitoring": true,
  "enable_gpio_monitoring": true,
  "gpio_pins": [],
  "custom_scripts": {},
  "alert_thresholds": {
    "cpu_percent": {
      "info": 30.0,
      "warning": 70.0,
      "critical": 85.0,
      "danger": 95.0
    },
    "memory_percent": {
      "info": 50.0,
      "warning": 75.0,
      "critical": 85.0,
      "danger": 95.0
    },
    "disk_percent": {
      "info": 60.0,
      "warning": 75.0,
      "critical": 85.0,
      "danger": 95.0
    },
    "temperature_celsius": {
      "info": 40.0,
      "warning": 60.0,
      "critical": 75.0,
      "danger": 85.0
    }
  }
}
EOF
    
    # Set ownership and permissions
    chown "$AGENT_USER:$AGENT_USER" "$CONFIG_DIR/agent_config.json"
    chmod 640 "$CONFIG_DIR/agent_config.json"
    
    print_success "Default configuration created"
    print_warning "Please edit $CONFIG_DIR/agent_config.json to configure your API endpoint and key"
}

setup_firewall() {
    print_status "Checking firewall configuration..."
    
    # Check if ufw is installed and active
    if command -v ufw >/dev/null 2>&1; then
        if ufw status | grep -q "Status: active"; then
            print_status "UFW is active, no changes needed for outbound connections"
        fi
    fi
    
    # Check if iptables has restrictive rules
    if iptables -L OUTPUT | grep -q "DROP\|REJECT"; then
        print_warning "Restrictive iptables rules detected. Ensure outbound HTTPS (443) and HTTP (80) are allowed"
    fi
}

show_completion_message() {
    echo
    print_success "Enhanced Raspberry Pi Monitoring Agent installation completed!"
    echo
    echo "Next steps:"
    echo "1. Edit the configuration file: $CONFIG_DIR/agent_config.json"
    echo "2. Set your API endpoint and API key"
    echo "3. Start the service: systemctl start $SERVICE_NAME"
    echo "4. Enable auto-start: systemctl enable $SERVICE_NAME"
    echo "5. Check status: systemctl status $SERVICE_NAME"
    echo "6. View logs: journalctl -u $SERVICE_NAME -f"
    echo
    echo "Configuration file location: $CONFIG_DIR/agent_config.json"
    echo "Log files location: $LOG_DIR/"
    echo "Data directory: $DATA_DIR/"
    echo
    echo "For help and documentation, visit: https://github.com/your-repo/rpi-monitoring"
    echo
}

# Main installation process
main() {
    echo "Enhanced Raspberry Pi Monitoring Agent Installer"
    echo "================================================"
    echo
    
    # Checks
    check_root
    check_raspberry_pi
    
    # Installation steps
    install_dependencies
    create_user
    create_directories
    install_agent
    setup_python_environment
    create_systemd_service
    setup_logrotate
    configure_agent
    setup_firewall
    
    # Completion
    show_completion_message
}

# Run main function
main "$@"
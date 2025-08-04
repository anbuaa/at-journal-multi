#!/bin/bash

# Production deployment script for Investment Journal
# This script sets up the application on a fresh Ubuntu 22.04 server

set -e  # Exit on any error

echo "🚀 Starting Investment Journal Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="investment-journal"
APP_USER="streamlit"
APP_DIR="/home/$APP_USER/$APP_NAME"
DOMAIN="${1:-localhost}"
EMAIL="${2:-admin@example.com}"

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check Ubuntu version
if ! grep -q "Ubuntu 22.04" /etc/os-release; then
    print_warning "This script is designed for Ubuntu 22.04. Continue? (y/n)"
    read -r response
    if [[ ! $response =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

print_status "Installing essential packages..."
sudo apt install -y git python3 python3-pip python3-venv nginx ufw curl software-properties-common

print_status "Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw --force enable

print_status "Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    sudo useradd -m -s /bin/bash $APP_USER
    sudo usermod -aG sudo $APP_USER
    print_success "User $APP_USER created"
else
    print_warning "User $APP_USER already exists"
fi

print_status "Setting up application directory..."
sudo -u $APP_USER mkdir -p $APP_DIR
sudo -u $APP_USER chmod 755 $APP_DIR

print_status "Cloning repository..."
if [ ! -d "$APP_DIR/.git" ]; then
    print_status "Please provide your GitHub repository URL:"
    read -r REPO_URL
    sudo -u $APP_USER git clone $REPO_URL $APP_DIR
else
    print_warning "Repository already exists, pulling latest changes..."
    sudo -u $APP_USER git -C $APP_DIR pull
fi

print_status "Setting up Python virtual environment..."
sudo -u $APP_USER python3 -m venv $APP_DIR/venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip

print_status "Installing Python dependencies..."
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

print_status "Testing application..."
print_status "Starting test server (will run for 10 seconds)..."
timeout 10 sudo -u $APP_USER $APP_DIR/venv/bin/streamlit run $APP_DIR/app.py --server.port=8501 --server.address=0.0.0.0 &
sleep 10
if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    print_success "Application health check passed"
else
    print_warning "Health check failed, but continuing..."
fi

print_status "Installing Node.js and PM2..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install pm2@latest -g

print_status "Creating PM2 ecosystem file..."
sudo -u $APP_USER cat > $APP_DIR/ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: '$APP_NAME',
    script: '$APP_DIR/venv/bin/streamlit',
    args: 'run $APP_DIR/app.py --server.port=8501 --server.address=0.0.0.0',
    cwd: '$APP_DIR',
    user: '$APP_USER',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PYTHONUNBUFFERED: '1'
    },
    error_file: '$APP_DIR/logs/error.log',
    out_file: '$APP_DIR/logs/out.log',
    log_file: '$APP_DIR/logs/combined.log'
  }]
};
EOF

print_status "Creating log directory..."
sudo -u $APP_USER mkdir -p $APP_DIR/logs

print_status "Starting application with PM2..."
sudo -u $APP_USER pm2 start $APP_DIR/ecosystem.config.js
sudo -u $APP_USER pm2 save
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u $APP_USER --hp /home/$APP_USER

print_status "Configuring NGINX..."
sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null << EOF
# HTTP server block (redirects to HTTPS)
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server block
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL certificates (will be configured by certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy strict-origin-when-cross-origin;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=main:10m rate=10r/s;
    limit_req zone=main burst=20 nodelay;

    # Proxy to Streamlit
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /_stcore/health {
        proxy_pass http://127.0.0.1:8501/_stcore/health;
        access_log off;
    }
}
EOF

print_status "Enabling NGINX site..."
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

print_status "Testing NGINX configuration..."
sudo nginx -t

if [ "$DOMAIN" != "localhost" ]; then
    print_status "Installing Certbot for SSL..."
    sudo apt install certbot python3-certbot-nginx -y
    
    print_status "Obtaining SSL certificate..."
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email $EMAIL
    
    print_status "Testing certificate renewal..."
    sudo certbot renew --dry-run
else
    print_warning "Skipping SSL setup for localhost"
    # Create a simple HTTP-only config for localhost
    sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null << EOF
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF
fi

print_status "Starting NGINX..."
sudo systemctl start nginx
sudo systemctl enable nginx

print_status "Creating backup script..."
sudo tee /home/$APP_USER/backup.sh > /dev/null << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/$APP_USER/backups"
APP_DIR="$APP_DIR"

mkdir -p \$BACKUP_DIR

# Backup databases
cp \$APP_DIR/*.db \$BACKUP_DIR/database_\$DATE.db 2>/dev/null || true

# Backup application code
tar -czf \$BACKUP_DIR/app_\$DATE.tar.gz \$APP_DIR

# Keep only last 7 days of backups
find \$BACKUP_DIR -name "*.db" -mtime +7 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

sudo chmod +x /home/$APP_USER/backup.sh
sudo chown $APP_USER:$APP_USER /home/$APP_USER/backup.sh

print_status "Setting up daily backups..."
sudo -u $APP_USER crontab -l 2>/dev/null | { cat; echo "0 2 * * * /home/$APP_USER/backup.sh"; } | sudo -u $APP_USER crontab -

print_status "Creating monitoring script..."
sudo tee /home/$APP_USER/monitor.sh > /dev/null << EOF
#!/bin/bash
echo "=== Investment Journal Status ==="
echo "Date: \$(date)"
echo ""
echo "=== PM2 Status ==="
pm2 status
echo ""
echo "=== NGINX Status ==="
sudo systemctl status nginx --no-pager -l
echo ""
echo "=== Disk Usage ==="
df -h
echo ""
echo "=== Memory Usage ==="
free -h
echo ""
echo "=== Application Health ==="
curl -f http://localhost:8501/_stcore/health && echo "Application: HEALTHY" || echo "Application: UNHEALTHY"
EOF

sudo chmod +x /home/$APP_USER/monitor.sh
sudo chown $APP_USER:$APP_USER /home/$APP_USER/monitor.sh

print_status "Installing fail2ban for security..."
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

print_status "Creating update script..."
sudo tee /home/$APP_USER/update.sh > /dev/null << EOF
#!/bin/bash
echo "Updating Investment Journal..."
cd $APP_DIR
git pull
$APP_DIR/venv/bin/pip install -r requirements.txt
pm2 restart $APP_NAME
echo "Update complete!"
EOF

sudo chmod +x /home/$APP_USER/update.sh
sudo chown $APP_USER:$APP_USER /home/$APP_USER/update.sh

print_success "Deployment completed successfully!"
echo ""
echo "📊 Investment Journal Status:"
echo "================================"
echo "🌐 Application URL: http://$DOMAIN"
if [ "$DOMAIN" != "localhost" ]; then
    echo "🔒 HTTPS URL: https://$DOMAIN"
fi
echo "👤 Application User: $APP_USER"
echo "📁 Application Directory: $APP_DIR"
echo "🔧 Process Manager: PM2"
echo "🌍 Web Server: NGINX"
echo ""
echo "📚 Useful Commands:"
echo "================================"
echo "# Check application status"
echo "sudo -u $APP_USER pm2 status"
echo ""
echo "# View application logs"
echo "sudo -u $APP_USER pm2 logs $APP_NAME"
echo ""
echo "# Restart application"
echo "sudo -u $APP_USER pm2 restart $APP_NAME"
echo ""
echo "# Update application"
echo "sudo -u $APP_USER /home/$APP_USER/update.sh"
echo ""
echo "# Monitor system"
echo "sudo -u $APP_USER /home/$APP_USER/monitor.sh"
echo ""
echo "# Manual backup"
echo "sudo -u $APP_USER /home/$APP_USER/backup.sh"
echo ""
echo "🔧 Configuration Files:"
echo "================================"
echo "NGINX Config: /etc/nginx/sites-available/$APP_NAME"
echo "PM2 Config: $APP_DIR/ecosystem.config.js"
echo "App Config: $APP_DIR/.streamlit/config.toml"
echo ""
print_success "Your Investment Journal is now live and ready to use!"

if [ "$DOMAIN" != "localhost" ]; then
    echo ""
    print_status "Don't forget to:"
    echo "1. Point your domain DNS to this server's IP address"
    echo "2. Create your first user account through the web interface"
    echo "3. Set up monitoring and alerts for production use"
fi
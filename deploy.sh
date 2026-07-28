#!/usr/bin/env bash
# ─── DigitalOcean Droplet Setup Script ───
# Run on a fresh Ubuntu 22.04/24.04 droplet
set -e

echo "═══ Installing Docker ═══"
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

echo "═══ Installing Nginx + Certbot ═══"
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx

echo "═══ Cloning repository ═══"
cd /opt
if [ -d "astrovakta-backened" ]; then
  cd astrovakta-backened && git pull
else
  git clone https://github.com/singhsonukumar6/astrovakta-backened.git
  cd astrovakta-backened
fi

echo "═══ Creating .env from example ═══"
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "  .env created. Edit it now: nano .env"
  echo "  Then run: docker compose up -d"
else
  echo "  .env already exists."
fi

echo "═══ Starting services ═══"
docker compose up -d --build

echo "═══ Setting up Nginx ═══"
sudo cp nginx.conf /etc/nginx/sites-available/astrovakta
sudo ln -sf /etc/nginx/sites-available/astrovakta /etc/nginx/sites-enabled/astrovakta
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

echo "═══ Getting SSL certificate ═══"
echo "Run: sudo certbot --nginx -d api.yourdomain.com"

echo ""
echo "═══ DONE! ═══"
echo "  API: http://$(curl -s ifconfig.me):8000/health"
echo "  Don't forget to:"
echo "    1. Edit .env with real Supabase URL + secrets"
echo "    2. Run: sudo certbot --nginx -d api.yourdomain.com"
echo "    3. Set up auto-renew: sudo systemctl enable certbot.timer"
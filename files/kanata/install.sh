# 1. Download the latest binary (x64)
curl -L https://github.com/jtroo/kanata/releases/latest/download/kanata -o kanata

# 2. Make it executable
chmod +x kanata

# 3. Move it to your path
sudo mv kanata /usr/local/bin/

sudo usermod -aG input $USER
sudo usermod -aG uinput $USER
# 🚀 Deployment Guide

Complete deployment instructions for the Telegram File Sharing Bot with Triple Force Subscription.

## 📋 Prerequisites

### 1. Telegram Setup
- **API Credentials**: Get from [my.telegram.org](https://my.telegram.org)
- **Bot Token**: Create bot with [@BotFather](https://t.me/BotFather)
- **Channel IDs**: Use [@userinfobot](https://t.me/userinfobot) to get channel IDs

### 2. Channel Requirements
- **1 Database Channel**: Store files (bot must be admin with all permissions)
- **3 Force Subscription Channels**: Users must join these (bot must be admin with invite permissions)

### 3. Database
- **MongoDB**: Required for data persistence
- Use MongoDB Atlas (free tier) or local MongoDB instance

## 🌐 Platform Deployments

### 1. 🚀 Heroku Deployment

#### One-Click Deploy
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

#### Manual Deploy
```bash
# Clone repository
git clone <your-repo-url>
cd file-sharing-bot

# Login to Heroku
heroku login

# Create app
heroku create your-bot-name

# Set environment variables
heroku config:set API_ID=your_api_id
heroku config:set API_HASH=your_api_hash
heroku config:set BOT_TOKEN=your_bot_token
heroku config:set OWNER_ID=your_user_id
heroku config:set CHANNEL_ID=your_channel_id
heroku config:set FORCE_SUB_CHANNEL_1=channel_1_id
heroku config:set FORCE_SUB_CHANNEL_2=channel_2_id
heroku config:set FORCE_SUB_CHANNEL_3=channel_3_id
heroku config:set DATABASE_URL=your_mongodb_url

# Deploy
git add .
git commit -m "Deploy bot"
git push heroku main

# Scale worker
heroku ps:scale worker=1
```

### 2. 🚂 Railway Deployment

#### One-Click Deploy
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/railway-template)

#### Manual Deploy
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create project
railway new

# Set environment variables
railway variables set API_ID=your_api_id
railway variables set API_HASH=your_api_hash
railway variables set BOT_TOKEN=your_bot_token
railway variables set OWNER_ID=your_user_id
railway variables set CHANNEL_ID=your_channel_id
railway variables set FORCE_SUB_CHANNEL_1=channel_1_id
railway variables set FORCE_SUB_CHANNEL_2=channel_2_id
railway variables set FORCE_SUB_CHANNEL_3=channel_3_id
railway variables set DATABASE_URL=your_mongodb_url

# Deploy
railway up
```

### 3. 🎨 Render Deployment

#### Setup
1. Fork this repository
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New" → "Web Service"
4. Connect your GitHub repository

#### Configuration
```yaml
# render.yaml
services:
  - type: worker
    name: telegram-bot
    env: python
    buildCommand: pip install -r deps.txt
    startCommand: python main.py
    envVars:
      - key: API_ID
        sync: false
      - key: API_HASH
        sync: false
      - key: BOT_TOKEN
        sync: false
      - key: OWNER_ID
        sync: false
      - key: CHANNEL_ID
        sync: false
      - key: FORCE_SUB_CHANNEL_1
        sync: false
      - key: FORCE_SUB_CHANNEL_2
        sync: false
      - key: FORCE_SUB_CHANNEL_3
        sync: false
      - key: DATABASE_URL
        sync: false
```

### 4. ☁️ Koyeb Deployment

#### One-Click Deploy
[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy)

#### Manual Deploy
```bash
# Install Koyeb CLI
curl -sSL https://cli.koyeb.com/install.sh | bash

# Login
koyeb login

# Create app
koyeb app create telegram-bot

# Deploy service
koyeb service create telegram-bot \
  --app telegram-bot \
  --git github.com/yourusername/file-sharing-bot \
  --git-branch main \
  --type worker \
  --instance-type nano \
  --env API_ID=your_api_id \
  --env API_HASH=your_api_hash \
  --env BOT_TOKEN=your_bot_token \
  --env OWNER_ID=your_user_id \
  --env CHANNEL_ID=your_channel_id \
  --env FORCE_SUB_CHANNEL_1=channel_1_id \
  --env FORCE_SUB_CHANNEL_2=channel_2_id \
  --env FORCE_SUB_CHANNEL_3=channel_3_id \
  --env DATABASE_URL=your_mongodb_url
```

### 5. 🖥️ VPS Deployment

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv git -y

# Clone repository
git clone <your-repo-url>
cd file-sharing-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r deps.txt

# Create systemd service
sudo nano /etc/systemd/system/telegram-bot.service
```

#### Systemd Service File
```ini
[Unit]
Description=Telegram File Sharing Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/file-sharing-bot
Environment=PATH=/home/ubuntu/file-sharing-bot/venv/bin
Environment=API_ID=your_api_id
Environment=API_HASH=your_api_hash
Environment=BOT_TOKEN=your_bot_token
Environment=OWNER_ID=your_user_id
Environment=CHANNEL_ID=your_channel_id
Environment=FORCE_SUB_CHANNEL_1=channel_1_id
Environment=FORCE_SUB_CHANNEL_2=channel_2_id
Environment=FORCE_SUB_CHANNEL_3=channel_3_id
Environment=DATABASE_URL=your_mongodb_url
ExecStart=/home/ubuntu/file-sharing-bot/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Start Service
```bash
# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Check status
sudo systemctl status telegram-bot

# View logs
sudo journalctl -u telegram-bot -f
```

#### Using PM2 (Alternative)
```bash
# Install PM2
npm install -g pm2

# Start bot with PM2
pm2 start main.py --name telegram-bot --interpreter python3

# Save PM2 configuration
pm2 save
pm2 startup

# Monitor
pm2 monit
```

### 6. 🐳 Docker Deployment

#### Local Docker
```bash
# Build image
docker build -t telegram-bot .

# Run container
docker run -d \
  --name telegram-bot \
  --restart unless-stopped \
  -e API_ID=your_api_id \
  -e API_HASH=your_api_hash \
  -e BOT_TOKEN=your_bot_token \
  -e OWNER_ID=your_user_id \
  -e CHANNEL_ID=your_channel_id \
  -e FORCE_SUB_CHANNEL_1=channel_1_id \
  -e FORCE_SUB_CHANNEL_2=channel_2_id \
  -e FORCE_SUB_CHANNEL_3=channel_3_id \
  -e DATABASE_URL=your_mongodb_url \
  -v $(pwd)/logs:/app/logs \
  telegram-bot
```

#### Docker Compose
```bash
# Create .env file
cp .env.example .env
# Edit .env with your values

# Start services
docker-compose up -d

# View logs
docker-compose logs -f bot
```

## 🗃️ Database Setup

### MongoDB Atlas (Recommended)
1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Create free cluster
3. Create database user
4. Get connection string
5. Replace `<password>` with your password
6. Use as `DATABASE_URL`

### Local MongoDB
```bash
# Install MongoDB
sudo apt install mongodb -y

# Start MongoDB
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Connection string
DATABASE_URL=mongodb://localhost:27017
```

## 🔧 Environment Variables

### Required Variables
```bash
API_ID=12345678                          # From my.telegram.org
API_HASH=abcdef1234567890abcdef1234567890  # From my.telegram.org
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqr   # From @BotFather
OWNER_ID=123456789                        # Your user ID
CHANNEL_ID=-1001234567890                 # Database channel
FORCE_SUB_CHANNEL_1=-1001111111111        # Force sub channel 1
FORCE_SUB_CHANNEL_2=-1002222222222        # Force sub channel 2
FORCE_SUB_CHANNEL_3=-1003333333333        # Force sub channel 3
DATABASE_URL=mongodb://localhost:27017    # MongoDB connection
```

### Optional Variables
```bash
DATABASE_NAME=file_sharing_bot            # Database name
ADMINS=123456789 987654321               # Admin user IDs
PROTECT_CONTENT=True                     # Content protection
AUTO_DELETE_TIME=3600                    # Auto-delete (seconds)
JOIN_REQUEST_ENABLED=False               # Join request feature
START_MESSAGE=Custom welcome message     # Custom start message
FORCE_SUB_MESSAGE=Custom force sub msg   # Custom force sub message
CUSTOM_CAPTION=Custom file caption       # Custom file caption
```

## 🔍 Getting Channel IDs

### Method 1: @userinfobot
1. Forward a message from your channel to [@userinfobot](https://t.me/userinfobot)
2. It will show the channel ID

### Method 2: Web Telegram
1. Open [web.telegram.org](https://web.telegram.org)
2. Go to your channel
3. Look at URL: `https://web.telegram.org/a/#-1001234567890`
4. The number after `#` is your channel ID

### Method 3: Bot API
1. Add [@RawDataBot](https://t.me/RawDataBot) to your channel
2. Send any message
3. Bot will reply with channel info including ID

## 🛠️ Post-Deployment Setup

### 1. Channel Configuration
- Add bot to database channel as admin with all permissions
- Add bot to force subscription channels as admin with invite permissions

### 2. Test Bot
```bash
# Start bot
/start

# Test admin commands (as owner)
/genlink - Reply to a file
/users - View statistics
/stats - Detailed stats
```

### 3. Monitoring
- Check logs regularly
- Monitor database usage
- Track user activity through admin commands

## 🚨 Troubleshooting

### Common Issues

#### Bot Not Starting
```bash
# Check environment variables
env | grep -E "(API_ID|API_HASH|BOT_TOKEN)"

# Check logs
tail -f logs/bot_*.log
```

#### Database Connection Issues
```bash
# Test MongoDB connection
python3 -c "from pymongo import MongoClient; print(MongoClient('your_mongodb_url').admin.command('hello'))"
```

#### Channel Access Issues
- Ensure bot is admin in all channels
- Check channel IDs are correct (negative numbers)
- Verify bot has required permissions

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 main.py
```

## 📊 Monitoring & Maintenance

### Log Management
```bash
# View live logs
tail -f logs/bot_*.log

# Rotate logs (daily automatic)
# Logs are automatically rotated daily
```

### Database Maintenance
```bash
# Check database size
# Use MongoDB Compass or CLI tools

# Backup database
mongodump --uri="your_mongodb_url"
```

### Updates
```bash
# Pull latest code
git pull origin main

# Restart service
sudo systemctl restart telegram-bot
# or
pm2 restart telegram-bot
```

## 🔐 Security Best Practices

1. **Environment Variables**: Never commit API keys to version control
2. **Database Access**: Use authentication and restrict access
3. **Server Security**: Keep system updated, use firewall
4. **Bot Permissions**: Grant minimal required permissions
5. **Log Security**: Protect log files from unauthorized access

## 📞 Support

If you encounter issues:
1. Check the logs for error messages
2. Verify all environment variables are set correctly
3. Ensure all channels are properly configured
4. Test database connectivity
5. Check bot permissions in channels

For additional help, refer to the documentation or create an issue in the repository.
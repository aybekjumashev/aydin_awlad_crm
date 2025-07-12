# .env.example - AYDIN AWLAD CRM Environment Variables

# ================================
# DJANGO SETTINGS
# ================================

# Django Secret Key (generate new one for production)
SECRET_KEY=django-insecure-your-secret-key-here

# Debug mode (set to False in production)
DEBUG=True

# Allowed hosts (comma-separated for production)
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# ================================
# TELEGRAM BOT SETTINGS
# ================================

# Get from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIjKlMnOpQrStUvWxYz

# Your domain for webhooks (must be HTTPS in production)
TELEGRAM_WEBHOOK_BASE_URL=https://yourdomain.com

# Bot username (without @)
TELEGRAM_BOT_USERNAME=aydinawlad_bot

# ================================
# DATABASE SETTINGS
# ================================

# For SQLite (default), leave empty
# For PostgreSQL:
# DATABASE_URL=postgres://user:password@localhost:5432/aydin_crm
# For MySQL:
# DATABASE_URL=mysql://user:password@localhost:3306/aydin_crm

# ================================
# EMAIL SETTINGS (Optional)
# ================================

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# ================================
# PRODUCTION SETTINGS
# ================================

# Use Redis for cache in production
# REDIS_URL=redis://localhost:6379/1

# Use real email backend in production
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# ================================
# SETUP INSTRUCTIONS
# ================================

# 1. Copy this file to .env
# 2. Fill in your actual values
# 3. Never commit .env to version control
# 4. For Telegram bot:
#    - Create bot with @BotFather
#    - Get token and put it in TELEGRAM_BOT_TOKEN
#    - Set webhook URL to https://yourdomain.com/telegram/webhook/
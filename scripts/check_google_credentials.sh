#!/bin/bash
# Check if Google OAuth credentials are configured

echo "🔍 Checking Google OAuth Configuration..."
echo

ENV_FILE="/Users/mr-jy/github/mission42-timesheet/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found"
    exit 1
fi

# Load .env file
source "$ENV_FILE"

# Check if credentials are set
if [ -z "$GOOGLE_CLIENT_ID" ] || [ "$GOOGLE_CLIENT_ID" = "YOUR_CLIENT_ID_HERE.apps.googleusercontent.com" ]; then
    echo "❌ GOOGLE_CLIENT_ID is not configured"
    echo "   Current value: $GOOGLE_CLIENT_ID"
    echo
    echo "👉 Please add your Client ID from Google Cloud Console"
    exit 1
else
    echo "✅ GOOGLE_CLIENT_ID is configured"
    echo "   Value: ${GOOGLE_CLIENT_ID:0:30}..."
fi

if [ -z "$GOOGLE_CLIENT_SECRET" ] || [ "$GOOGLE_CLIENT_SECRET" = "GOCSPX-YOUR_CLIENT_SECRET_HERE" ]; then
    echo "❌ GOOGLE_CLIENT_SECRET is not configured"
    echo
    echo "👉 Please add your Client Secret from Google Cloud Console"
    exit 1
else
    echo "✅ GOOGLE_CLIENT_SECRET is configured"
    echo "   Value: GOCSPX-***************"
fi

if [ -n "$GOOGLE_REDIRECT_URI" ]; then
    echo "✅ GOOGLE_REDIRECT_URI is configured"
    echo "   Value: $GOOGLE_REDIRECT_URI"
fi

if [ -n "$ENCRYPTION_KEY" ]; then
    echo "✅ ENCRYPTION_KEY is configured"
else
    echo "⚠️  ENCRYPTION_KEY is not set"
    echo "   Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
fi

echo
echo "================================================"
echo "✅ Google OAuth is properly configured!"
echo "================================================"
echo
echo "Next steps:"
echo "  1. Make sure FastAPI is running:"
echo "     uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo
echo "  2. Connect your Google Calendar:"
echo "     open http://localhost:8000/oauth/calendar/init"
echo
echo "  3. Connect your Gmail:"
echo "     open http://localhost:8000/oauth/gmail/init"
echo

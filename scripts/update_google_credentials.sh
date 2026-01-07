#!/bin/bash
# Update Google OAuth Credentials in .env file

echo "================================================"
echo "🔑 Update Google OAuth Credentials"
echo "================================================"
echo
echo "This script will update your .env file with Google credentials."
echo
echo "Please enter your credentials from Google Cloud Console:"
echo

# Ask for Client ID
read -p "Google Client ID: " CLIENT_ID

# Ask for Client Secret
read -s -p "Google Client Secret: " CLIENT_SECRET
echo

# Validate inputs
if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
    echo
    echo "❌ Error: Both Client ID and Client Secret are required"
    exit 1
fi

# Check if .env file exists
ENV_FILE="/Users/mr-jy/github/mission42-timesheet/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Backup the .env file
cp "$ENV_FILE" "$ENV_FILE.backup"
echo
echo "✅ Created backup: .env.backup"

# Update the credentials using sed
sed -i '' "s|GOOGLE_CLIENT_ID=.*|GOOGLE_CLIENT_ID=$CLIENT_ID|" "$ENV_FILE"
sed -i '' "s|GOOGLE_CLIENT_SECRET=.*|GOOGLE_CLIENT_SECRET=$CLIENT_SECRET|" "$ENV_FILE"

echo "✅ Updated .env file with your credentials"
echo

# Verify the update
echo "📋 Current Google OAuth configuration:"
echo
grep "GOOGLE_CLIENT_ID\|GOOGLE_CLIENT_SECRET\|GOOGLE_REDIRECT_URI" "$ENV_FILE"
echo

echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo
echo "Next steps:"
echo "  1. Restart FastAPI:"
echo "     pkill -f uvicorn"
echo "     uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo
echo "  2. Connect your Google account:"
echo "     open http://localhost:8000/oauth/calendar/init"
echo "     open http://localhost:8000/oauth/gmail/init"
echo

# OAuth Setup Guide

Complete guide for setting up OAuth authentication for Google Calendar, Gmail, and GitHub integrations.

## Table of Contents

- [Overview](#overview)
- [Google OAuth Setup](#google-oauth-setup)
- [GitHub OAuth Setup](#github-oauth-setup)
- [WakaTime API Key](#wakatime-api-key)
- [Testing OAuth Flow](#testing-oauth-flow)
- [Troubleshooting](#troubleshooting)

## Overview

Mission42 Timesheet requires OAuth authentication for:
- **Google Calendar** - Fetch meeting data
- **Gmail** - Fetch sent email data
- **GitHub** - Fetch commit and issue data (using Personal Access Token)
- **WakaTime** - Fetch coding activity (using API Key)

## Google OAuth Setup

Google Calendar and Gmail use the same OAuth credentials.

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Enter project name: "Mission42 Timesheet"
4. Click **Create**
5. Select the newly created project

### Step 2: Enable Required APIs

1. Navigate to **APIs & Services** → **Library**
2. Search for and enable:
   - **Google Calendar API**
   - **Gmail API**

#### Enable Google Calendar API:
1. Search "Google Calendar API"
2. Click on it
3. Click **Enable**

#### Enable Gmail API:
1. Search "Gmail API"
2. Click on it
3. Click **Enable**

### Step 3: Configure OAuth Consent Screen

1. Navigate to **APIs & Services** → **OAuth consent screen**
2. Choose **User Type**:
   - **Internal** (if using Google Workspace)
   - **External** (for personal Gmail accounts)
3. Click **Create**

#### App Information:
- **App name**: Mission42 Timesheet
- **User support email**: Your email
- **Developer contact email**: Your email

#### Scopes:
Click **Add or Remove Scopes** and add:
- `https://www.googleapis.com/auth/calendar.readonly`
- `https://www.googleapis.com/auth/gmail.readonly`

Click **Update** → **Save and Continue**

#### Test Users (for External apps):
Add your Gmail address as a test user.

Click **Save and Continue**

### Step 4: Create OAuth Credentials

1. Navigate to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Application type: **Web application**
4. Name: "Mission42 Timesheet Web Client"

#### Authorized redirect URIs:
Add the following redirect URIs:
```
http://localhost:8000/oauth/google/callback
http://localhost:8000/oauth/calendar/callback
http://localhost:8000/oauth/gmail/callback
```

5. Click **Create**

#### Save Credentials:
You'll see a modal with:
- **Client ID**: `xxxxx.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-xxxxxxxxxxxxxxxxxxxxx`

**Copy these values immediately!**

### Step 5: Add to Environment Variables

Edit your `.env` file:

```bash
# Google OAuth (Calendar & Gmail)
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/google/callback
```

### Step 6: Generate Encryption Key

OAuth tokens are stored encrypted in PocketBase. Generate an encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add to `.env`:
```bash
ENCRYPTION_KEY=your-generated-key-here
```

### Step 7: Restart Application

```bash
# Restart FastAPI
python app/main.py
```

## GitHub OAuth Setup

GitHub uses Personal Access Tokens instead of OAuth.

### Step 1: Create Personal Access Token

1. Go to [GitHub Settings](https://github.com/settings/tokens)
2. Click **Generate new token** → **Generate new token (classic)**
3. Note: "Mission42 Timesheet"
4. Expiration: Choose duration (recommend 90 days or No expiration)

#### Select Scopes:
For **private repositories**:
- ✓ **repo** (Full control of private repositories)

For **public repositories only**:
- ✓ **public_repo** (Access public repositories)

#### Additional scopes (optional):
- ✓ **read:user** (Read user profile data)

5. Click **Generate token**

#### Save Token:
Copy the token immediately (format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

**Warning**: You can't view this token again!

### Step 2: Add to Environment Variables

Edit your `.env` file:

```bash
# GitHub API
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_USERNAME=your-github-username
```

### Step 3: Configure Monitored Repositories

In PocketBase admin UI:

1. Navigate to **Collections** → **settings**
2. Find setting with key "github_repositories"
3. Edit value to comma-separated list:
   ```
   owner1/repo1,owner2/repo2,your-username/your-repo
   ```
4. Save

Example:
```
facebook/react,microsoft/vscode,your-username/mission42-timesheet
```

## WakaTime API Key

WakaTime tracks coding activity across IDEs.

### Step 1: Get API Key

1. Go to [WakaTime Settings](https://wakatime.com/settings/api-key)
2. Log in if needed
3. Copy your **Secret API Key**

Format: `waka_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 2: Add to Environment Variables

Edit your `.env` file:

```bash
# WakaTime API
WAKATIME_API_KEY=waka_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 3: Install WakaTime Plugin

Install WakaTime plugin in your IDE:
- **VS Code**: [WakaTime Extension](https://marketplace.visualstudio.com/items?itemName=WakaTime.vscode-wakatime)
- **JetBrains**: Settings → Plugins → Search "WakaTime"
- **Vim**: https://github.com/wakatime/vim-wakatime
- **Other IDEs**: https://wakatime.com/plugins

Enter your API key when prompted.

## Testing OAuth Flow

### Test Google Calendar/Gmail Authentication

1. Start FastAPI application:
   ```bash
   python app/main.py
   ```

2. Navigate to OAuth initialization endpoint:
   ```bash
   # For Calendar
   open http://localhost:8000/oauth/calendar/init

   # For Gmail
   open http://localhost:8000/oauth/gmail/init
   ```

3. You'll be redirected to Google's consent screen
4. Sign in with your Google account
5. Click **Allow** to grant permissions
6. You'll be redirected back to the application
7. OAuth token will be saved encrypted in PocketBase

### Verify Token Storage

1. Open PocketBase admin UI: http://127.0.0.1:8090/_/
2. Navigate to **Collections** → **calendar_accounts** or **email_accounts**
3. You should see a record with:
   - Your email address
   - **encrypted_token** field populated
   - **last_sync** will update after first fetch

### Test Data Fetching

Manually trigger a fetch to test:

```bash
curl -X POST http://localhost:8000/process/manual
```

Check logs for successful fetching:
```bash
tail -f logs/app.log
```

You should see:
```
[calendar] Fetched X events, created Y new records
[gmail] Fetched X events, created Y new records
```

### Test GitHub Access

Test GitHub token:

```bash
curl -H "Authorization: token ghp_xxxxx" https://api.github.com/user
```

Should return your GitHub user info.

### Test WakaTime Access

Test WakaTime API key:

```bash
curl -H "Authorization: Bearer waka_xxxxx" \
  https://wakatime.com/api/v1/users/current
```

Should return your WakaTime user info.

## Troubleshooting

### Google OAuth Errors

#### Error: "redirect_uri_mismatch"

**Cause**: Redirect URI not configured in Google Cloud Console

**Solution**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **Credentials**
2. Edit your OAuth client
3. Add exact redirect URI from error message
4. Save changes
5. Try again

#### Error: "access_denied"

**Cause**: User clicked "Deny" on consent screen

**Solution**:
- Try OAuth flow again
- Ensure you click "Allow" on consent screen

#### Error: "invalid_client"

**Cause**: Wrong Client ID or Client Secret

**Solution**:
- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in `.env`
- Regenerate credentials if needed
- Restart application

### Token Expiration

#### Symptoms:
- Fetching stops working after some time
- "Invalid credentials" errors in logs

#### Solution:
Google OAuth tokens expire after a period. Re-authenticate:

1. Navigate to OAuth init endpoint again
2. Complete OAuth flow
3. New token will be saved

#### Refresh Tokens:
The application uses refresh tokens to automatically renew access tokens. If this fails:
- Delete old token from PocketBase
- Re-authenticate through OAuth flow

### GitHub Token Issues

#### Error: "Bad credentials"

**Cause**: Invalid or expired token

**Solution**:
1. Regenerate token on GitHub
2. Update GITHUB_TOKEN in `.env`
3. Restart application

#### Error: "Resource not accessible by integration"

**Cause**: Insufficient token permissions

**Solution**:
1. Create new token with correct scopes:
   - For private repos: **repo** scope
   - For public repos: **public_repo** scope
2. Update `.env`
3. Restart

### WakaTime Issues

#### Error: "Unauthorized"

**Cause**: Invalid API key

**Solution**:
1. Get new API key from https://wakatime.com/settings/api-key
2. Update WAKATIME_API_KEY in `.env`
3. Restart application

#### No data being tracked

**Cause**: WakaTime plugin not installed or not activated

**Solution**:
1. Install WakaTime plugin in your IDE
2. Enter API key when prompted
3. Restart IDE
4. Start coding - data should appear within 10 minutes

### Encryption Key Issues

#### Error: "ENCRYPTION_KEY must be set"

**Cause**: Missing encryption key in `.env`

**Solution**:
```bash
# Generate key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
echo "ENCRYPTION_KEY=<generated-key>" >> .env

# Restart application
```

#### Error: "Invalid token" when decrypting

**Cause**: Encryption key changed after tokens were encrypted

**Solution**:
1. Delete all encrypted tokens from PocketBase
2. Re-authenticate through OAuth flows
3. Tokens will be encrypted with new key

## Security Best Practices

### 1. Keep Credentials Secure

- **Never commit** `.env` file to git
- Use different credentials for dev/prod
- Rotate tokens periodically

### 2. Use Minimal Permissions

Request only the OAuth scopes you need:
- Calendar: `calendar.readonly`
- Gmail: `gmail.readonly`
- GitHub: `public_repo` if possible (not `repo`)

### 3. Monitor Token Usage

Regularly check:
- Google Cloud Console → **APIs & Services** → **Dashboard**
- Monitor API usage quotas
- Review access logs

### 4. Backup Encryption Key

The ENCRYPTION_KEY is critical:
- Back it up securely
- Don't share it
- If lost, all OAuth tokens must be re-authenticated

### 5. Use Environment-Specific Configs

For production:
```bash
# Production .env
GOOGLE_REDIRECT_URI=https://yourdomain.com/oauth/google/callback
FASTAPI_HOST=0.0.0.0
FASTAPI_DEBUG=false
```

## OAuth Flow Diagram

```
User → FastAPI (/oauth/calendar/init)
         ↓
      Google Consent Screen
         ↓ (user clicks Allow)
      Google redirects to /oauth/calendar/callback
         ↓
      FastAPI receives authorization code
         ↓
      FastAPI exchanges code for tokens
         ↓
      Tokens encrypted and stored in PocketBase
         ↓
      Success! Token ready for API calls
```

## Support

For OAuth issues:
- Google OAuth: https://developers.google.com/identity/protocols/oauth2
- GitHub Tokens: https://docs.github.com/en/authentication
- WakaTime: https://wakatime.com/help
- Project Issues: https://github.com/ZisenisDigital/mission42-timesheet/issues

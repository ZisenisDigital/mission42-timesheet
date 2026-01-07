# Authentication System - Secure Your Timesheet! 🔐

## ✅ **Authentication Now Active**

Your timesheet is now **protected with PocketBase authentication**!

---

## 🚀 **Quick Start**

### **1. Open the Login Page:**
```bash
open http://localhost:8000/login
```

### **2. Login with Default Accounts:**

**Viewer Account** (Read-only access):
- Email: `viewer@example.com`
- Password: `ViewerPass123`

**Admin Account** (Full access):
- Email: `admin@example.com`
- Password: `admin123456`

### **3. Access Protected Timesheet:**
After login, you'll be automatically redirected to:
```bash
http://localhost:8000/timesheet/current
```

---

## 🔒 **What's Protected**

### **Requires Login:**
- ✅ `/timesheet/current` - Current month timesheet
- ✅ `/timesheet/month/{year}/{month}` - Specific month timesheet

### **Public (No Login):**
- ❌ `/login` - Login page (obviously!)
- ❌ `/health` - Health check
- ❌ `/` - API homepage
- ❌ `/docs` - API documentation

---

## 📱 **How Authentication Works**

### **Login Flow:**
1. User opens `/timesheet/current`
2. Not logged in? → Redirected to `/login`
3. Enter email and password
4. Click "Sign In"
5. Authentication token saved in cookie (14 days)
6. Redirected to timesheet
7. Done! ✅

### **Session:**
- Token stored in HTTP-only cookie (secure!)
- Expires after 14 days
- Auto-renewed on each request
- Same as PocketBase standard

---

## 👥 **User Accounts**

### **Current Users:**

**1. Viewer User** (Created earlier):
```
Email: viewer@example.com
Password: ViewerPass123
```
- Read-only access
- Can view timesheets
- Cannot modify data

**2. Admin User** (PocketBase superuser):
```
Email: admin@example.com
Password: admin123456
```
- Full access
- Can view and modify
- Can access PocketBase admin panel

---

## ➕ **Add More Users**

### **Method 1: Via PocketBase Admin UI**
```bash
open http://127.0.0.1:8090/_/
# Login: admin@example.com / admin123456
# Go to "Users" collection
# Click "New Record"
# Fill in email and password
# Save
```

### **Method 2: Via Python Script**
```python
from pocketbase import PocketBase

pb = PocketBase('http://127.0.0.1:8090')
pb.admins.auth_with_password('admin@example.com', 'admin123456')

# Create new user
new_user = pb.collection('users').create({
    'email': 'newuser@example.com',
    'password': 'newpassword123',
    'passwordConfirm': 'newpassword123',
    'emailVisibility': True,
})

print(f"User created: {new_user.email}")
```

---

## 🔓 **Logout**

### **Via Browser:**
```bash
# Send POST request to logout
curl -X POST http://localhost:8000/auth/logout
```

### **Or Simply:**
- Clear browser cookies
- Close browser (if session-based)

---

## 🛡️ **Security Features**

### **What's Secure:**
- ✅ **HTTP-only cookies** - JavaScript can't access tokens
- ✅ **PocketBase JWT tokens** - Industry standard
- ✅ **14-day expiration** - Auto-logout after 2 weeks
- ✅ **Encrypted passwords** - PocketBase handles hashing
- ✅ **Protected endpoints** - Can't access without login

### **What's NOT Secure (Yet):**
- ⚠️ **HTTP (not HTTPS)** - Only for local testing!
- ⚠️ **CORS allows all** - Need to restrict in production
- ⚠️ **No rate limiting** - Could add brute-force protection

---

## 🔧 **API Endpoints**

### **Authentication:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/login` | Show login page |
| POST | `/auth/login` | Login with email/password |
| POST | `/auth/logout` | Logout (clear cookie) |
| GET | `/auth/me` | Get current user info |

### **Protected Endpoints:**
| Method | Endpoint | Requires Auth |
|--------|----------|---------------|
| GET | `/timesheet/current` | ✅ Yes |
| GET | `/timesheet/month/{year}/{month}` | ✅ Yes |

---

## 💡 **Testing Authentication**

### **Test 1: Access Without Login**
```bash
# Try to access timesheet without login
curl -v http://localhost:8000/timesheet/current
# Should redirect to /login (303 redirect)
```

### **Test 2: Login via API**
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"viewer@example.com","password":"ViewerPass123"}' \
  -c cookies.txt

# Access timesheet (with cookie)
curl -b cookies.txt http://localhost:8000/timesheet/current
# Should return HTML timesheet!
```

### **Test 3: Login via Browser**
```bash
# Open login page
open http://localhost:8000/login

# Enter:
# Email: viewer@example.com
# Password: ViewerPass123

# Click "Sign In"
# Should redirect to timesheet! ✅
```

---

## 🎯 **Common Workflows**

### **Workflow 1: Share Timesheet with Client**

**Give them viewer access:**
1. Email: `viewer@example.com`
2. Password: `ViewerPass123`
3. URL: `http://localhost:8000/login`

*(For production, create a specific user for each client)*

### **Workflow 2: Personal Use**

**Just you:**
1. Login once: `open http://localhost:8000/login`
2. Cookie saved for 14 days
3. Access anytime: `open http://localhost:8000/timesheet/current`
4. No re-login needed for 2 weeks!

### **Workflow 3: Team Access**

**Multiple users:**
1. Create user for each team member (via PocketBase admin)
2. Give them credentials
3. They login and access their timesheet
4. Each has their own session

---

## 🚨 **Troubleshooting**

### **Problem: "Not authenticated" error**

**Solution:**
```bash
# Clear cookies and login again
open http://localhost:8000/login
```

### **Problem: "Invalid email or password"**

**Check:**
- Email is correct (case-sensitive!)
- Password is correct
- User exists in PocketBase

**Verify user exists:**
```bash
open http://127.0.0.1:8090/_/
# Check "Users" collection
```

### **Problem: Redirect loop**

**Solution:**
```bash
# Clear all cookies
# Restart browser
# Try login again
```

---

## 📊 **What Changed**

### **Before:**
```bash
# Anyone could access timesheet
open http://localhost:8000/timesheet/current
# ✅ Worked without login
```

### **After:**
```bash
# Must login first
open http://localhost:8000/timesheet/current
# ↩️ Redirects to /login
# ✅ Login required!
```

---

## ✨ **Summary**

**You now have:**
- ✅ Login page with PocketBase authentication
- ✅ Protected timesheet endpoints
- ✅ Secure cookie-based sessions (14 days)
- ✅ Multiple user support
- ✅ Easy to share with controlled access

**Default accounts:**
- 📧 Viewer: `viewer@example.com` / `ViewerPass123`
- 👤 Admin: `admin@example.com` / `admin123456`

**Quick access:**
```bash
# Login
open http://localhost:8000/login

# View timesheet (after login)
open http://localhost:8000/timesheet/current
```

**Authentication is now active!** 🔐

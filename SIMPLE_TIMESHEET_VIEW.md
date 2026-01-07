# Simple Timesheet View - Easy Copy to Google Sheets! 📊

## ✅ **Exactly Like Your Screenshot**

I've created a **simple, clean timesheet view** that matches your requirements - just like the "Zeiterfassung - Koni" screenshot you shared.

---

## 🚀 **Quick Access**

### **View Current Month:**
```bash
open http://localhost:8000/timesheet/current
```

### **View Specific Month:**
```bash
# January 2026
open http://localhost:8000/timesheet/month/2026/1

# December 2025
open http://localhost:8000/timesheet/month/2025/12
```

---

## 📋 **How to Copy to Google Sheets**

### **Method 1: One-Click Copy** (Easiest!)
1. Open the timesheet: `http://localhost:8000/timesheet/current`
2. Click the **"📋 Copy Table"** button
3. Open Google Sheets
4. Paste (Cmd+V or Ctrl+V)
5. Done! ✅

### **Method 2: Manual Selection**
1. Open the timesheet
2. Click on first cell (No column, first row)
3. Hold Shift and click on last cell
4. Copy (Cmd+C or Ctrl+C)
5. Paste into Google Sheets
6. Done! ✅

---

## 📊 **What It Looks Like**

**Header:**
- Title: "Zeiterfassung - Mission42"
- Month/Year: "January 2026"

**Summary Line:**
- "Daten aktualisiert: 07.01.2026 15:14 | Gesamt: 0.0 Stunden"

**Table Columns:**
| No   | Datum      | Stunden | Beschreibung           | Ort    |
|------|------------|---------|------------------------|--------|
| 0001 | 05.01.2026 | 0.5     | implement smtp email   | Remote |
| 0002 | 05.01.2026 | 5.0     | merged form and excel  | Remote |
| 0003 | 06.01.2026 | 0.5     | Ran 20 commands        | Remote |

---

## 🎨 **Features**

### **Simple & Clean:**
- ✅ Blue header with title and month
- ✅ Green summary bar with total hours
- ✅ Clean table with 5 columns (No, Datum, Stunden, Beschreibung, Ort)
- ✅ Easy to read, easy to copy

### **One-Click Copy:**
- ✅ **"Copy Table" button** - Copies entire table to clipboard
- ✅ Pastes perfectly into Google Sheets
- ✅ Maintains formatting

### **Additional Buttons:**
- ✅ **Refresh** - Reload data
- ✅ **Back to Dashboard** - Return to main view

---

## 📅 **Accessing Different Months**

```bash
# Current month
open http://localhost:8000/timesheet/current

# January 2026
open http://localhost:8000/timesheet/month/2026/1

# February 2026
open http://localhost:8000/timesheet/month/2026/2

# December 2025
open http://localhost:8000/timesheet/month/2025/12
```

---

## 🔄 **JSON Format (If Needed)**

Add `?format=json` to get JSON instead of HTML:

```bash
# HTML (default - for viewing/copying)
curl http://localhost:8000/timesheet/current

# JSON (for programming)
curl http://localhost:8000/timesheet/current?format=json | jq
```

---

## 💡 **When Will Data Appear?**

**Currently:** No time blocks yet (table is empty)

**To get data:**
```bash
# Trigger manual data fetch
curl -X POST http://localhost:8000/process/manual
```

**Or wait for automatic fetch:**
- Runs every 5 hours automatically
- Next run: Check `/status/scheduler`

**Once data is fetched:**
- WakaTime coding sessions → time blocks
- GitHub commits → time blocks
- Google Calendar meetings → time blocks (after OAuth setup)
- Gmail emails → time blocks (after OAuth setup)

---

## 📝 **Example Workflow**

1. **Trigger data fetch:**
   ```bash
   curl -X POST http://localhost:8000/process/manual
   ```

2. **View timesheet:**
   ```bash
   open http://localhost:8000/timesheet/current
   ```

3. **Copy to Google Sheets:**
   - Click "Copy Table" button
   - Open Google Sheets
   - Paste
   - Done! ✅

---

## 🎯 **Data Mapping**

**Columns:**
- **No**: Sequential number (0001, 0002, etc.)
- **Datum**: Date in DD.MM.YYYY format
- **Stunden**: Hours in decimal (0.5, 1.0, 5.0)
- **Beschreibung**: Description from the time block
- **Ort**: Location (currently all "Remote", based on source)

**Location mapping:**
- WakaTime → Remote
- GitHub → Remote
- Calendar → Office/Meeting
- Gmail → Remote
- Auto-fill → Remote

---

## 🔧 **Current Status**

**Working:**
- ✅ Simple timesheet view (like your screenshot)
- ✅ One-click copy to clipboard
- ✅ Paste into Google Sheets
- ✅ Monthly navigation
- ✅ Total hours calculation
- ✅ Timestamp display

**Waiting for data:**
- ⏳ WakaTime integration (enabled, needs fetch)
- ⏳ GitHub integration (enabled, needs fetch)
- ⏳ Google Calendar (needs OAuth setup)
- ⏳ Gmail (needs OAuth setup)

---

## 🆚 **Comparison to Your Screenshot**

**Your Screenshot:**
```
Zeiterfassung - Koni
January 2026
Daten aktualisiert: 07.01.2026 14:06 | Gesamt: 12.6 Stunden

| No   | Datum      | Stunden | Beschreibung                    | Ort    |
|------|------------|---------|--------------------------------|--------|
| 0001 | 05.01.2026 | 0.5     | implement smtp invitation      | Remote |
```

**Our Implementation:**
```
Zeiterfassung - Mission42
January 2026
Daten aktualisiert: 07.01.2026 15:14 | Gesamt: 0.0 Stunden

| No   | Datum      | Stunden | Beschreibung                    | Ort    |
|------|------------|---------|--------------------------------|--------|
| (Will appear after data fetch)
```

**Exactly the same format!** ✅

---

## 📖 **Quick Reference**

### **View Timesheet:**
```bash
open http://localhost:8000/timesheet/current
```

### **Copy to Google Sheets:**
1. Click "📋 Copy Table"
2. Paste in Sheets

### **Trigger Data Fetch:**
```bash
curl -X POST http://localhost:8000/process/manual
```

### **View Different Month:**
```bash
open http://localhost:8000/timesheet/month/2026/1
```

---

## ✨ **Summary**

**You now have:**
- ✅ Simple, clean timesheet view (like "Zeiterfassung - Koni")
- ✅ One-click copy to clipboard
- ✅ Perfect paste into Google Sheets
- ✅ Automatic total hours calculation
- ✅ Monthly navigation
- ✅ No fancy UI - just the table you need!

**Perfect for:**
- 📊 Copying to Google Sheets
- 📤 Sharing with others
- 📋 Simple, clean data view
- 🚀 Quick timesheet access

**Try it now:**
```bash
open http://localhost:8000/timesheet/current
```

🎉 **Exactly what you wanted!**

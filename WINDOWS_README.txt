# Malaysia Stock Dashboard - Windows Setup Guide

## Quick Start

### Option 1: Using run.bat (Recommended)

1. **Copy folder to Windows:**
   Copy the entire `dashboard` folder to your Windows PC (e.g., C:\StockDashboard)

2. **Install Python** (if not installed):
   Download from: https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH"
   - ✅ Check "Install pip"

3. **Install dependencies:**
   Open Command Prompt and run:
   ```
   pip install flask flask-cors yfinance pandas numpy
   ```

4. **Run the dashboard:**
   Double-click `run.bat` or run in CMD:
   ```
   run.bat
   ```

5. **Open in browser:**
   ```
   http://192.168.250.208:6000
   ```

---

### Option 2: Using run-auto.bat (Auto-detect IP)

This version tries to auto-detect your network IP.

---

## Manual Run

```cmd
cd C:\StockDashboard
python app.py 192.168.250.208 6000
```

---

## Files

| File | Purpose |
|------|---------|
| app.py | Main server |
| index.html | Dashboard UI |
| run.bat | Quick start script |
| run-auto.bat | Auto-detect IP |

---

## Troubleshooting

**"Python not found"**
- Install Python and check "Add to PATH"

**"Port already in use"**
- Change port: `python app.py 192.168.250.208 6001`

**"Cannot access from other devices"**
- Make sure Windows Firewall allows Python
- Or disable firewall temporarily for testing

---

## Access URLs

- **This PC:** http://localhost:6000
- **Network:** http://192.168.250.208:6000
- **Phone:** http://192.168.250.208:6000 (same WiFi)

---

*Last updated: 2026-03-22*

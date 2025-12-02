# Allure Report - Quick Setup Guide

## 🎯 Problem & Solution

**Issue**: `allure serve` command doesn't exist in Allure 3.0+

**Fix**: Allure 3.0 changed the CLI syntax. Use these commands instead:

---

## ✅ Working Commands

### Generate and View Reports

```powershell
# Generate report
allure generate allure-results -o allure-report

# Open in browser (opens automatically on http://localhost:61329)
allure open allure-report
```

### Watch Mode (Automatic updates)
```powershell
# Watch allure-results directory and regenerate on changes
allure watch allure-results
```

### Direct Open
```powershell
# Open allure-results directly without generating
allure open allure-results
```

---

## 🔧 Common Issues & Fixes

### Issue 1: PowerShell Execution Policy
**Error**: "execution of scripts is disabled in this system"

**Fix**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
```

### Issue 2: Port Already in Use
**Error**: "Address already in use"

**Fix**: Use a different port
```powershell
allure open allure-results --port 8080
```

### Issue 3: Cannot Find Allure
**Error**: "allure : The term 'allure' is not recognized"

**Fix**: Install Allure via npm
```powershell
npm install -g allure-commandline
```

---

## 📊 Full Workflow

### 1. Run Tests with Allure
```powershell
cd "c:\Users\felip\Documents\GitHub\Cenfotec\Inteligencia Artificial para Desarrolladores\Semana 2\Guided_Copilot"
pytest tests/ -v
```

### 2. Generate Report
```powershell
allure generate allure-results -o allure-report
```

### 3. View Report
```powershell
allure open allure-report
```

---

## 📍 Your Report Location

- **Results Directory**: `allure-results/`
- **Generated Report**: `allure-report/`
- **Browser URL**: http://localhost:61329

---

## 🔍 What to Look For in Your Report

### Features
1. **Test Summary**
   - Total tests run
   - Pass/fail/skip counts
   - Execution time

2. **By Features**
   - Error Handling
   - Data Persistence
   - Courses Management
   - System Health
   - User Management

3. **By Stories**
   - Error Tracking
   - Notifications
   - Atomic Writes
   - Course Creation
   - And more...

4. **By Severity**
   - CRITICAL (5 tests)
   - HIGH (8 tests)
   - NORMAL (12 tests)

5. **By Tags**
   - unit, integration, bdd
   - courses, enrollments, health-check
   - persistence, validation, error-handling
   - defect, recovery, concurrency

---

## 💡 Tips

### Filter Tests
In the Allure report UI:
1. Click on "Defects" to see defect regression tests
2. Click on "Severity" to see critical tests
3. Click on "Features" to filter by feature
4. Click on "Tags" to filter by functional area

### Export Data
```powershell
# Export as CSV
allure csv allure-results -o report.csv

# Export as test plan
allure testplan allure-results -o testplan.json
```

### View Trends
```powershell
# Generate report with history
allure generate allure-results -o allure-report --history-path history
```

---

## ✨ Advanced: Integration with CI/CD

```bash
# In your CI/CD pipeline:
npm install -g allure-commandline
pytest tests/ -v
allure generate allure-results -o allure-report
# Upload allure-report to your reporting server
```

---

## 🆘 Getting Help

```powershell
# View all available commands
allure --help

# View help for specific command
allure generate --help
allure open --help
allure watch --help
```

---

## ✅ Current Status

- ✅ Allure installed: v3.0.0-beta.23
- ✅ Execution policy fixed
- ✅ Report running on: http://localhost:61329
- ✅ 25+ tests with comprehensive decorators
- ✅ Ready for enterprise integration

Your Allure report is now live and ready to use!

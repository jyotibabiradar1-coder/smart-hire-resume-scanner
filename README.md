# 💼 SmartHire - Intelligent Talent Acquisition & ATS Platform

**SmartHire** is a modern, full-stack recruitment intelligence platform designed with human-centric SaaS aesthetics, automated key skill extraction, and candidate pipeline tracking.

---

## 🌐 Quick Access (Website Link) - https://smart-hire-updatedgit-58ivvraqqneqrdzxvhtbw3.streamlit.app

When the application is running, open any web browser and navigate to:

- **Local Access Link:** [http://localhost:8501](http://localhost:8501)
- **Alternate Loopback:** [http://127.0.0.1:8501](http://127.0.0.1:8501)
- **Network Link:** `http://10.26.53.94:8501` *(for devices on your local Wi-Fi / network)*

---

## 🚀 How to Run SmartHire

### Option 1: 1-Click Windows Launcher (Easiest)
Double-click [`run.bat`](file:///c:/Users/birad/OneDrive/Desktop/project/run.bat) in the project folder. It initializes the database, starts the server, and automatically pops open your browser.

### Option 2: Command Line (PowerShell / Command Prompt)
```cmd
cd "C:\Users\birad\OneDrive\Desktop\project"
py -3.13 -m streamlit run app.py
```

### Option 3: PowerShell Script
```powershell
.\start_app.ps1
```

---

## 🔑 Default Login Credentials

| Role | Username | Password | Privileges |
| :--- | :--- | :--- | :--- |
| **HR Lead** | `admin` | `Admin@12345` | Role benchmarking, dynamic candidate cards, skill breakdown, dossier export, team management |
| **Applicant** | `candidate1` | `Candidate@12345` | Document upload, hiring pipeline progress stepper, ATS match score, evaluation dossier |

---

## 🎨 New Features & Human-Crafted SaaS Enhancements

1. **Modern SaaS UI System:**
   - Slate & electric blue visual identity with `Plus Jakarta Sans` typography.
   - Interactive top navigation bar with live status indicator and user badge.
   - Elimination of generic AI tropes in favor of clean corporate card architecture.

2. **Smart Skill Extraction Engine:**
   - Detects over 40+ industry competencies (Python, SQL, React, Docker, NLP, Scikit-Learn, AWS, etc.).
   - Displays matched skill pills on candidate cards and role specifications.

3. **Dynamic View Modes & Recruiter Filters:**
   - Toggle between **Dynamic Profile Cards** (avatars, skill chips, confidence bars) and **Data Table View**.
   - Interactive minimum score slider and live candidate search bar.

4. **Applicant Experience (Lever/Greenhouse Style):**
   - 4-stage visual hiring pipeline stepper (`Application Submitted` $\rightarrow$ `Resume Screened` $\rightarrow$ `Recruiter Review` $\rightarrow$ `Interview Stage`).
   - Profile summary with detected strengths and ATS optimization advice.

5. **SmartHire Executive Evaluation Dossier (PDF):**
   - Clean, professional ReportLab PDF layout with confidential branding, score cards, detected skills, and benchmark excerpt.

@echo off
title SmartHire - Talent Acquisition and ATS Platform
cd /d "%~dp0"

echo ======================================================================
echo    Starting SmartHire - Talent Acquisition Platform
echo ======================================================================
echo.

:: Detect Python Runtime
py -3.13 --version >nul 2>&1
if %errorlevel%==0 (
    set PY_CMD=py -3.13
) else (
    set PY_CMD=python
)

echo Using Python runtime: %PY_CMD%

:: Ensure database schema is ready
echo Initializing SmartHire database...
%PY_CMD% fix_db.py >nul 2>&1

:: Open Browser automatically in background after a brief delay
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8501"

:: Launch Streamlit
echo Launching SmartHire on http://localhost:8501 ...
%PY_CMD% -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --browser.serverAddress localhost

pause

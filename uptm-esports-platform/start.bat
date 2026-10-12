@echo off
title UPTM Esports Platform
cd /d "%~dp0"

echo =======================================================
echo   UPTM SECURE COMPETITIVE GAMING PLATFORM
echo =======================================================
echo.
echo Sedang memeriksa Python...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [RALAT] Python tidak dijumpai di komputer anda!
    echo Sila muat turun dan install Python dari https://www.python.org/
    echo PENTING: Pastikan anda tandakan (tick) kotak "Add Python to PATH" semasa install.
    echo.
    pause
    exit /b 1
)

echo Memulakan pelayan website...
echo Buka pelayar web (browser) anda di: http://127.0.0.1:5000
echo Tekan Ctrl + C di terminal ini untuk berhenti.
echo.
python run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [INFO] Jika terdapat ralat modul tidak dijumpai, sila klik dua kali 'setup.bat'
    echo        atau taip perintah: pip install -r requirements.txt
    echo.
    pause
)

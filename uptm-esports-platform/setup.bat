@echo off
title UPTM Esports Platform - Setup
cd /d "%~dp0"

echo =======================================================
echo   UPTM ESPORTS PLATFORM - PEMASANGAN DEPENDENCIES
echo =======================================================
echo.
echo Sedang memasang dependencies dari requirements.txt...
pip install -r requirements.txt

echo.
echo =======================================================
echo Pemasangan selesai! 
echo Anda kini boleh klik dua kali fail 'start.bat' 
echo atau jalankan perintah: python run.py
echo =======================================================
pause

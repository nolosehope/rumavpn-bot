@echo off
title RumaVPN Bot
cd /d "%~dp0"

rem Find Python: PATH first, then default install location
set "PY=python"
python --version >nul 2>&1
if errorlevel 1 set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

if not exist ".env" (
    echo [ERROR] .env file not found. Copy .env.example to .env and fill it in.
    pause
    exit /b 1
)

echo === RumaVPN bot starting... ===
echo To stop the bot: close this window or press Ctrl+C.
echo.

"%PY%" bot.py

echo.
echo === Bot stopped. If you see an error above, fix it and run again. ===
pause

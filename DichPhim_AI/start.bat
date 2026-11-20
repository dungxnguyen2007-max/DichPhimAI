@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================
echo       DICH PHIM TRUC TIEP - AI
echo ==========================================
if "%OPENAI_API_KEY%"=="" (
    echo.
    echo Chua co OPENAI_API_KEY.
    echo Hay mo file .env.example, dien API key,
    echo sau do dat bien moi truong OPENAI_API_KEY.
    echo.
    pause
    exit /b 1
)
python server.py
pause

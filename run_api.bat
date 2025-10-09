@echo off
echo Starting Telegram Reviews API Server...
echo.

REM Проверяем установлен ли Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ to run this server
    pause
    exit /b 1
)

REM Устанавливаем зависимости если requirements.txt существует
if exist requirements.txt (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo WARNING: requirements.txt not found, attempting to run anyway...
)

echo.
echo Starting API server on http://localhost:5000
echo API endpoints:
echo - http://localhost:5000/api/reviews (последние 7 отзывов)
echo - http://localhost:5000/api/reviews/latest (последний отзыв)
echo.
echo Press Ctrl+C to stop the server
echo.

python api_server.py

pause
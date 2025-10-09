@echo off
echo Deploying Reviews API to hosting...
echo.

REM Инициализируем git репозиторий если его нет
if not exist .git (
    echo Initializing git repository...
    git init
    git add .
    git commit -m "Initial commit: Reviews API server"
)

REM Добавляем удаленный репозиторий (замените на ваш)
echo.
echo Add your hosting repository:
echo Example: git remote add origin https://github.com/yourusername/reviews-api.git
echo.
echo Then push:
echo git push origin main
echo.

REM Пример для Railway CLI
echo.
echo For Railway deployment:
echo railway login
echo railway link
echo railway up
echo.

pause
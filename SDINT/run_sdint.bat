@echo off
echo ===================================================
echo   SDINT - Social Data Intelligence Platform Launcher
echo ===================================================
echo.
echo Checking prerequisites...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH! Please install Python 3.10+
    pause
    exit /b
)

node --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Node.js is not installed or not in PATH! Please install Node.js 18+
    pause
    exit /b
)

echo.
echo Starting Backend Server (Flask)...
cd backend
echo Installing backend dependencies...
python -m pip install -r requirements.txt >nul
echo Downloading SpaCy model (en_core_web_sm)...
python -m spacy download en_core_web_sm >nul

start "SDINT Backend" cmd /k "title SDINT Backend Server && python app.py"

cd ../frontend
echo.
echo Starting Frontend Server (Vite/React)...
echo Installing frontend dependencies...
call npm install >nul

start "SDINT Frontend" cmd /k "title SDINT Frontend Server && npm run dev"

echo.
echo ===================================================
echo SDINT is now running! 
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:5000
echo ===================================================
echo Press any key to exit this launcher (Servers will keep running in separate windows).
pause >nul

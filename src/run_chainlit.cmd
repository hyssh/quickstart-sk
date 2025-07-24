@echo off
REM Set venv path (relative to this script)
set VENV_PATH=..\.venv

REM List of ports to check
set PORTS=8089 8087 8091 8086 8000 8501

REM Prompt user to check for active processes
set /p CHECKPORTS="Do you want to check which processes are using ports %PORTS%? (y/n): "
if /i "%CHECKPORTS%"=="y" (
    for %%P in (%PORTS%) do (
        echo Checking port %%P...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%%P') do (
            echo Port %%P is used by PID: %%a
        )
    )
    pause
    set /p KILLPORTS="Do you want to kill these processes? (y/n): "
    if /i "%KILLPORTS%"=="y" (
        for %%P in (%PORTS%) do (
            for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%%P') do (
                echo Killing process on port %%P with PID %%a
                taskkill /PID %%a /F >nul 2>&1
            )
        )
        echo Ports checked and processes killed if found.
    ) else (
        echo Skipping killing processes.
    )
) else (
    echo Skipping port check.
)

echo Starting services with venv: %VENV_PATH%
echo.

REM Start MCP servers
echo Starting Weather MCP Server...
start "Weather MCP" cmd /k "call %VENV_PATH%\Scripts\activate && python ./mcpservers/weather.py"

echo Starting LocalTime MCP Server...
start "LocalTime MCP" cmd /k "call %VENV_PATH%\Scripts\activate && python ./mcpservers/localtime.py"

echo Starting Azure Data Explorer MCP Server...
start "Azure Data Explorer MCP" cmd /k "call %VENV_PATH%\Scripts\activate && python ./mcpservers/azuredataexproler.py"

REM Start backend server
echo Starting Backend Server...
start "Backend Server" cmd /k "call %VENV_PATH%\Scripts\activate && python ./backend/server.py"

REM Wait a moment for servers to start
timeout /t 3 /nobreak >nul

REM Start Chainlit frontend
echo Starting Chainlit Frontend...
start "Chainlit App" cmd /k "call %VENV_PATH%\Scripts\activate && chainlit run ./frontend/app.py"

echo All services started. Check individual terminal windows for status.

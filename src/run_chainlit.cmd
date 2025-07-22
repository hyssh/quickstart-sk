@echo off
REM Set default conda environment name (can be overridden)
if "%CONDA_ENV%"=="" set CONDA_ENV=sk

echo Starting services with conda environment: %CONDA_ENV%
echo.

REM Start MCP servers
echo Starting Weather MCP Server...
start "Weather MCP" cmd /k "conda activate %CONDA_ENV% && python ./mcpservers/weather.py"

echo Starting LocalTime MCP Server...
start "LocalTime MCP" cmd /k "conda activate %CONDA_ENV% && python ./mcpservers/localtime.py"

echo Starting Azure Data Explorer MCP Server...
start "Azure Data Explorer MCP" cmd /k "conda activate %CONDA_ENV% && python ./mcpservers/azuredataexproler.py"

REM Start backend server
echo Starting Backend Server...
start "Backend Server" cmd /k "conda activate %CONDA_ENV% && python ./backend/server.py"

REM Wait a moment for servers to start
timeout /t 3 /nobreak >nul

REM Start Chainlit frontend
echo Starting Chainlit Frontend...
start "Chainlit App" cmd /k "conda activate %CONDA_ENV% && chainlit run ./frontend/app.py"

echo All services started. Check individual terminal windows for status. 

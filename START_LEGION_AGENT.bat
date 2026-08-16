@echo off
title Legion Agent Server Port 8099
color 0A
chcp 65001 >nul 2>&1

echo.
echo ====================================================
echo   LEGION AGENT SERVER STARTUP
echo ====================================================
echo.

set VENV_PY=C:\WEB CASE STUDY\.venv\Scripts\python.exe
set SCRIPT=C:\WEB CASE STUDY\legion_agent_server.py
set PORT=8099
set LOGFILE=C:\WEB CASE STUDY\legion_agent.log

echo [1/6] Locating Python...
if exist "%VENV_PY%" (
    set PYTHON="%VENV_PY%"
    echo       OK: WCS venv
    goto check_script
)
if exist "E:\WEB CASE STUDY\.venv\Scripts\python.exe" (
    set PYTHON="E:\WEB CASE STUDY\.venv\Scripts\python.exe"
    echo       OK: E-drive venv
    goto check_script
)
if exist "C:\STUDIES_BACKUP\.venv_fresh\Scripts\python.exe" (
    set PYTHON="C:\STUDIES_BACKUP\.venv_fresh\Scripts\python.exe"
    echo       OK: venv_fresh
    goto check_script
)
where python >nul 2>&1
if %errorlevel%==0 (
    set PYTHON=python
    echo       WARN: system Python
    goto check_script
)
echo       ERROR: No Python found
pause
exit /b 1

:check_script
echo [2/6] Checking script...
if not exist "%SCRIPT%" (
    echo       ERROR: legion_agent_server.py not found
    echo       Path: %SCRIPT%
    echo       Extract the zip to C:\WEB CASE STUDY\
    pause
    exit /b 1
)
echo       OK

echo [3/6] Checking dependencies...
%PYTHON% -c "import fastmcp,fastapi,uvicorn,duckdb,lancedb,logfire,httpx,numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Installing...
    %PYTHON% -m pip install fastmcp fastapi uvicorn duckdb lancedb logfire httpx numpy --quiet --no-warn-script-location
    if %errorlevel% neq 0 (
        echo       ERROR: pip install failed
        echo       Run: %PYTHON% -m pip install fastmcp fastapi uvicorn duckdb lancedb logfire httpx numpy
        pause
        exit /b 1
    )
    echo       OK: Installed
) else (
    echo       OK: All present
)

echo [4/6] Checking port %PORT%...
netstat -ano 2>nul | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo       Clearing port %PORT%...
    for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
        taskkill /PID %%p /F >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo       Cleared
) else (
    echo       OK: Port free
)

echo [5/6] Checking services...
%PYTHON% -c "import socket; s=socket.socket(); s.settimeout(0.5); r=s.connect_ex(('127.0.0.1',1234)); s.close(); print('      OK  LM Studio :1234' if r==0 else '      WARN LM Studio :1234 DOWN')"
%PYTHON% -c "import socket; s=socket.socket(); s.settimeout(0.5); r=s.connect_ex(('127.0.0.1',11434)); s.close(); print('      OK  Ollama :11434' if r==0 else '      WARN Ollama :11434 DOWN')"
%PYTHON% -c "import socket; s=socket.socket(); s.settimeout(0.5); r=s.connect_ex(('127.0.0.1',8002)); s.close(); print('      OK  mcp_api_server :8002' if r==0 else '      INFO mcp_api_server :8002 DOWN')"
%PYTHON% -c "import socket; s=socket.socket(); s.settimeout(0.5); r=s.connect_ex(('127.0.0.1',6379)); s.close(); print('      OK  Ray GCS :6379' if r==0 else '      INFO Ray :6379 DOWN')"

echo [6/6] Starting...
echo.
echo ====================================================
echo   PORT  : %PORT%
echo   SSE   : http://127.0.0.1:%PORT%/mcp/sse
echo   REST  : http://127.0.0.1:%PORT%/health
echo   STACK : http://127.0.0.1:%PORT%/stack
echo   LOG   : %LOGFILE%
echo ====================================================
echo.

set MCP_API_BASE=http://127.0.0.1:8001
set MCP_TOOLS_EXEC=http://127.0.0.1:8002/tools/execute
set LM_STUDIO_BASE=http://127.0.0.1:1234
set OLLAMA_BASE=http://127.0.0.1:11434
set AGENT_PORT=%PORT%
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

%PYTHON% -X utf8 "%SCRIPT%" >> "%LOGFILE%" 2>&1

echo.
echo Stopped. Log: %LOGFILE%
echo.
pause
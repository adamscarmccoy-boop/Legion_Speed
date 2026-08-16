@echo off
title Legion Agent Server — Port 8099
color 0A

echo.
echo ============================================================
echo   LEGION AGENT SERVER — STARTUP
echo ============================================================
echo.

:: ── CONFIG ──────────────────────────────────────────────────
set VENV="C:\WEB CASE STUDY\.venv\Scripts\python.exe"
set SCRIPT="C:\WEB CASE STUDY\legion_agent_server.py"
set PORT="8099"
set LOGFILE="C:\WEB CASE STUDY\legion_agent_server.log"

:: ── CHECK VENV ───────────────────────────────────────────────
echo [1/5] Checking venv...
if not exist "%VENV%" (
    echo ERROR: venv not found at %VENV%
    echo Fix: python -m venv "C:\WEB CASE STUDY\.venv"
    echo      "%VENV%" -m pip install fastmcp fastapi uvicorn duckdb lancedb logfire httpx numpy
    pause
    exit /b 1
)
echo       OK: %VENV%

:: ── CHECK SCRIPT ─────────────────────────────────────────────
echo [2/5] Checking server script...
if not exist "%SCRIPT%" (
    echo ERROR: legion_agent_server.py not found at %SCRIPT%
    echo Copy it from the Office Agent sandbox output.
    pause
    exit /b 1
)
echo       OK: %SCRIPT%

:: ── CHECK PORT FREE ──────────────────────────────────────────
echo [3/5] Checking port %PORT%...
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo       WARNING: Port %PORT% already in use — killing old process...
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
        taskkill /PID %%p /F >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo       Cleared.
) else (
    echo       OK: Port %PORT% is free.
)

:: ── CHECK DEPENDENCIES ───────────────────────────────────────
echo [4/5] Checking Python dependencies...
"%VENV%" -c "import fastmcp, fastapi, uvicorn, duckdb, lancedb, logfire, httpx, numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Installing missing dependencies...
    "%VENV%" -m pip install fastmcp fastapi uvicorn duckdb lancedb logfire httpx numpy --quiet
    if %errorlevel% neq 0 (
        echo ERROR: pip install failed. Check your internet connection.
        pause
        exit /b 1
    )
    echo       Dependencies installed.
) else (
    echo       OK: All dependencies present.
)

:: ── CHECK OPTIONAL SERVICES ───────────────────────────────────
echo [5/5] Checking optional services...

:: LM Studio
powershell -Command "try { $r=(New-Object Net.Sockets.TcpClient('127.0.0.1',1234)); $r.Close(); Write-Host '      OK: LM Studio :1234 UP' } catch { Write-Host '      WARN: LM Studio :1234 DOWN (embed will fail)' }"

:: Ollama
powershell -Command "try { $r=(New-Object Net.Sockets.TcpClient('127.0.0.1',11434)); $r.Close(); Write-Host '      OK: Ollama :11434 UP' } catch { Write-Host '      WARN: Ollama :11434 DOWN (inference will fail)' }"

:: mcp_api_server
powershell -Command "try { $r=(New-Object Net.Sockets.TcpClient('127.0.0.1',8002)); $r.Close(); Write-Host '      OK: mcp_api_server :8002 UP (proxy_tool available)' } catch { Write-Host '      INFO: mcp_api_server :8002 DOWN (proxy_tool will degrade gracefully)' }"

:: Ray
powershell -Command "try { $r=(New-Object Net.Sockets.TcpClient('127.0.0.1',6379)); $r.Close(); Write-Host '      OK: Ray GCS :6379 UP' } catch { Write-Host '      INFO: Ray :6379 DOWN' }"

echo.
echo ============================================================
echo   STARTING LEGION AGENT SERVER ON PORT %PORT%
echo   MCP SSE  : http://127.0.0.1:%PORT%/mcp/sse
echo   REST API : http://127.0.0.1:%PORT%/health
echo   Stack    : http://127.0.0.1:%PORT%/stack
echo   Log      : %LOGFILE%
echo ============================================================
echo.
echo   Add to mcp_config.json:
echo   "legion-agent": {
echo     "command": "%VENV%",
echo     "args": ["%SCRIPT%", "--sse"],
echo     "env": { "AGENT_PORT": "%PORT%" }
echo   }
echo.
echo   Press Ctrl+C to stop.
echo ============================================================
echo.

:: ── LAUNCH ───────────────────────────────────────────────────
set MCP_API_BASE=http://127.0.0.1:8001
set MCP_TOOLS_EXEC=http://127.0.0.1:8002/tools/execute
set LM_STUDIO_BASE=http://127.0.0.1:1234
set OLLAMA_BASE=http://127.0.0.1:11434
set AGENT_PORT=%PORT%

"%VENV%" "%SCRIPT%" 2>&1 | tee "%LOGFILE%"

echo.
echo Legion Agent Server stopped.
pause
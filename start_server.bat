@echo off
echo ============================================
echo   Starting Legion API Server (port 8080)
echo ============================================

cd /d "C:\web case study"

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set the agent provider (nvidia, lmstudio, or gemini)
set AGENT_PROVIDER=lmstudio
set AGENT_RECURSION_LIMIT=3
set API_SERVER_HOST=0.0.0.0
set API_SERVER_PORT=8080

REM Start the OpenAI-compatible API server
"C:\WEB CASE STUDY\.venv\Scripts\python.exe" openai_api_server.py

pause

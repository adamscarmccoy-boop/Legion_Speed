@echo off
echo ============================================
echo   Starting OpenWebUI
echo ============================================

cd /d "C:\web case study"

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set environment variables
set DATA_DIR=%cd%\openwebui_data
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

REM Enable authentication & initial admin signup screen
set WEBUI_AUTH=True
set ENABLE_SIGNUP=True
set DEFAULT_USER_ROLE=admin

REM Configure OpenAI API & Cloudflare AI Gateway endpoints
set OPENAI_API_BASE_URLS=http://127.0.0.1:8080/v1;https://gateway.ai.cloudflare.com/v1/668c939d165191cd68621f7d04c32d0e/ray-bridge-ai/openai
set OPENAI_API_KEYS=sk-legion;cfk_MC8tKsaJVrsYuMalJrLeQdIZZOpv0KIehSpcZXr71162010d
set WEBUI_NAME=Legion Sovereign Cloudflare AI
set WEBUI_SECRET_KEY=qqfknsYNN/ReomVyVietNQ/h5lgJo7su

REM Start OpenWebUI on port 3000
echo Starting OpenWebUI at http://localhost:3000 ...
"C:\WEB CASE STUDY\.venv\Scripts\open-webui.exe" serve --host 0.0.0.0 --port 3000

pause

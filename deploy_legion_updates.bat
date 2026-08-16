@echo off
:: ============================================================================
:: SOVEREIGN ARCHITECTURE — AUTOMATED BATCH DEPLOYMENT & VERIFICATION SCRIPT
:: ============================================================================
TITLE Sovereign Legion Updates Deployer

echo ================================================================================
echo 🚀 DEPLOYING LEGION SOVEREIGN UPDATES TO HARDCODED PATHS
echo ================================================================================

set DEPLOY_DIR=%~dp0

:: Create Target Directories if Missing
if not exist "C:\STUDIES_BACKUP\Legion-Jacked-Pipeline" mkdir "C:\STUDIES_BACKUP\Legion-Jacked-Pipeline"
if not exist "C:\WEB CASE STUDY" mkdir "C:\WEB CASE STUDY"
if not exist "C:\Users\%USERNAME%\.lmstudio\plugins\rag-v1\src" mkdir "C:\Users\%USERNAME%\.lmstudio\plugins\rag-v1\src"

echo.
echo [1/4] Copying Legion Graph & MCP Servers to Root A...
copy /Y "%DEPLOY_DIR%legion_graph_fixed.py" "C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\legion_graph_fixed.py"
copy /Y "%DEPLOY_DIR%mcp_rag_server.py" "C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\mcp_rag_server.py"
copy /Y "%DEPLOY_DIR%mcp_api_server.py" "C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\mcp_api_server.py"

echo.
echo [2/4] Copying Swarm Gateway & C++ Kernel Sources to Root B...
copy /Y "%DEPLOY_DIR%mcp_swarm_gateway_v2.py" "C:\WEB CASE STUDY\mcp_swarm_gateway_v2.py"
copy /Y "%DEPLOY_DIR%sovereign_pipeline_suite_real.py" "C:\WEB CASE STUDY\sovereign_pipeline_suite_real.py"
copy /Y "%DEPLOY_DIR%codebase_lakehouse_query.py" "C:\WEB CASE STUDY\codebase_lakehouse_query.py"
copy /Y "%DEPLOY_DIR%sovereign_real_benchmark.cpp" "C:\WEB CASE STUDY\sovereign_real_benchmark.cpp"

echo.
echo [3/4] Copying Fixed TS Prompt Preprocessor to LM Studio Plugins...
copy /Y "%DEPLOY_DIR%promptPreprocessor_fixed.ts" "C:\Users\%USERNAME%\.lmstudio\plugins\rag-v1\src\promptPreprocessor.ts"

echo.
echo [4/4] Executing Post-Deployment Verification & LM Studio Self-Healing Probe...
if exist "C:\WEB CASE STUDY\.venv\Scripts\python.exe" (
    "C:\WEB CASE STUDY\.venv\Scripts\python.exe" "%DEPLOY_DIR%verify_and_heal_deployment.py"
) else (
    python "%DEPLOY_DIR%verify_and_heal_deployment.py"
)

echo.
echo ================================================================================
echo ✅ DEPLOYMENT COMPLETE & VERIFIED
echo ================================================================================
pause

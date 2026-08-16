@echo off
:: ============================================================================
:: SOVEREIGN AOT (AHEAD-OF-TIME) MASTER COMPILER — WINDOWS 64-BIT
:: ============================================================================
TITLE Sovereign AOT Master Build Suite

echo ================================================================================
echo ⚡ COMPILING ALL SOVEREIGN C++/CUDA MODULES TO NATIVE AOT BINARIES (.DLL / .EXE)
echo ================================================================================
echo.

set BUILD_DIR=%~dp0
cd /d "%BUILD_DIR%"

:: Check for MinGW g++ compiler
where g++ >nul 2>nul
if %errorlevel%==0 (
    echo [FOUND COMPILER] MinGW g++ detected. Building with AVX2 optimizations...
    echo.
    echo [1/4] Compiling sovereign_aot_kernel.dll...
    g++ -O3 -shared -mavx2 sovereign_aot_kernel_win.cpp -o sovereign_aot_kernel.dll
    
    echo [2/4] Compiling sovereign_real_benchmark.dll...
    g++ -O3 -shared -mavx2 sovereign_real_benchmark.cpp -o sovereign_real_benchmark.dll
    
    echo [3/4] Compiling sovereign_engine.exe (Bare-Metal Executable)...
    g++ -O3 -mavx2 sovereign_baremetal_engine.cpp -o sovereign_engine.exe
    
    goto VERIFY_AOT
)

:: Check for MSVC cl.exe compiler
where cl >nul 2>nul
if %errorlevel%==0 (
    echo [FOUND COMPILER] Microsoft Visual C++ (cl.exe) detected. Building with /O2...
    echo.
    echo [1/4] Compiling sovereign_aot_kernel.dll...
    cl.exe /LD /O2 /EHsc /std:c++17 /arch:AVX2 sovereign_aot_kernel_win.cpp /Fe:sovereign_aot_kernel.dll
    
    echo [2/4] Compiling sovereign_real_benchmark.dll...
    cl.exe /LD /O2 /EHsc /std:c++17 /arch:AVX2 sovereign_real_benchmark.cpp /Fe:sovereign_real_benchmark.dll
    
    echo [3/4] Compiling sovereign_engine.exe (Bare-Metal Executable)...
    cl.exe /O2 /EHsc /std:c++17 /arch:AVX2 sovereign_baremetal_engine.cpp /Fe:sovereign_engine.exe
    
    goto VERIFY_AOT
)

echo ❌ ERROR: Neither g++ (MinGW) nor cl.exe (MSVC) was found in your PATH.
echo    Please install Build Tools or run this from 'x64 Native Tools Command Prompt'.
pause
exit /b 1

:VERIFY_AOT
echo.
echo ================================================================================
echo ✅ AOT COMPILATION VERIFICATION
echo ================================================================================
if exist sovereign_aot_kernel.dll (
    echo [✅ AOT READY] sovereign_aot_kernel.dll
) else (
    echo [❌ FAILED] sovereign_aot_kernel.dll
)

if exist sovereign_real_benchmark.dll (
    echo [✅ AOT READY] sovereign_real_benchmark.dll
) else (
    echo [❌ FAILED] sovereign_real_benchmark.dll
)

if exist sovereign_engine.exe (
    echo [✅ AOT READY] sovereign_engine.exe
) else (
    echo [❌ FAILED] sovereign_engine.exe
)

echo.
echo 🚀 All binaries pre-compiled Ahead-Of-Time. Zero JIT runtime delay!
echo ================================================================================
pause

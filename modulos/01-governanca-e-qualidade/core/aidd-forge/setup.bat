@echo off
setlocal

where python >nul 2>&1
if errorlevel 1 (
    echo [aidd-forge] Python nao encontrado no PATH. Instale Python 3.10+ e tente novamente.
    pause >nul
    exit /b 1
)

set "AIDD_LOG=%TEMP%\aidd_forge_setup.log"
python -m aidd_forge.cli init >"%AIDD_LOG%" 2>&1

if errorlevel 1 (
    echo [aidd-forge] Nao foi possivel configurar o projeto automaticamente.
    echo [aidd-forge] Detalhes em: %AIDD_LOG%
    pause >nul
    exit /b 1
)

type "%AIDD_LOG%"
color 0A
echo.
echo   [OK] AIDD Forge configurado com sucesso neste projeto.
echo.
color
pause >nul

endlocal
exit /b 0

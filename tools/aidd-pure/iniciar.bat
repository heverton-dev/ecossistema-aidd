@echo off
chcp 65001 > nul
title AIDD Generator — Interface Web

echo ======================================================================
echo          ⚡ AIDD PROJECT GENERATOR — INTERFACE WEB LOCAL
echo ======================================================================
echo.
echo  [1/2] Verificando ambiente Python...

:: Detectar Python
set PYTHON_EXE=python
if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
)

%PYTHON_EXE% --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Python nao encontrado no sistema. Por favor, instale o Python 3.10+
    echo        e certifique-se de marcar "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo  [2/2] Iniciando servidor e abrindo navegador...
echo.
echo  A interface abrira automaticamente em: http://localhost:5000
echo  Mantenha esta janela aberta enquanto estiver usando o aplicativo.
echo  (Para encerrar, basta fechar esta janela ou pressionar CTRL+C)
echo.
echo ======================================================================
echo.

:: Executa o entrypoint que inicia o Flask e abre o navegador automaticamente
%PYTHON_EXE% web_app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [AVISO] O servidor foi finalizado.
    pause
)

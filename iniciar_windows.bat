@echo off
chcp 65001 >nul
title MuniCertificados — Municipalidad de San Roque (Area de Redes)

echo ============================================================================
echo   MuniCertificados — Sistema Institucional de Emision de Certificados
echo   Municipalidad de San Roque, Corrientes — Area de Modernizacion y Redes
echo ============================================================================
echo.

cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] No se detecto Python instalado en el sistema.
    echo Instale Python 3.11 o superior desde https://www.python.org/downloads/
    echo asegurandose de marcar la casilla "Add Python to PATH".
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creando entorno virtual local (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo [2/3] Instalando dependencias desde requirements.txt...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\pip.exe" install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Fallo la instalacion de dependencias.
        pause
        exit /b 1
    )
) else (
    echo [1/2] Entorno virtual detectado (.venv). Verificando dependencias...
    ".venv\Scripts\pip.exe" install -q -r requirements.txt
)

echo [OK] Iniciando MuniCertificados...
".venv\Scripts\python.exe" main.py
if %errorlevel% neq 0 (
    echo.
    echo [AVISO] La aplicacion se cerro con un codigo de error.
    pause
)

@echo off
chcp 65001 >nul
title Compilador de Instalador — MuniCertificados (Windows)

echo ============================================================================
echo   Compilando MuniCertificados.exe + Instalador Setup_MuniCertificados_v1.0.exe
echo   Municipalidad de San Roque — Area de Modernizacion y Redes
echo ============================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creando entorno virtual (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

echo [2/4] Instalando dependencias y PyInstaller...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\pip.exe" install -r requirements.txt pyinstaller
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)

echo [3/4] Compilando ejecutable con PyInstaller (MuniCertificados.spec)...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
".venv\Scripts\pyinstaller.exe" --clean --noconfirm MuniCertificados.spec
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la compilacion con PyInstaller.
    pause
    exit /b 1
)

echo [4/4] Buscando Inno Setup 6 (ISCC.exe) para generar el instalador...
set "ISCC_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
if "%ISCC_PATH%"=="" (
    where ISCC.exe >nul 2>nul
    if %errorlevel% equ 0 set "ISCC_PATH=ISCC.exe"
)

if "%ISCC_PATH%"=="" (
    echo.
    echo [AVISO] No se encontro Inno Setup 6 instalado.
    echo El ejecutable portable ya fue generado exitosamente en:
    echo   dist\MuniCertificados\MuniCertificados.exe
    echo Para generar el instalador Setup_MuniCertificados_v1.0.exe, instale Inno Setup 6
    echo desde https://jrsoftware.org/isdl.php y vuelva a ejecutar este script.
    pause
    exit /b 0
)

"%ISCC_PATH%" installer.iss
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la compilacion del instalador con Inno Setup.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo   [EXITO] Compilacion finalizada correctamente:
echo   - Portable:   dist\MuniCertificados\MuniCertificados.exe
echo   - Instalador: dist_installer\Setup_MuniCertificados_v1.0.exe
echo ============================================================================
pause

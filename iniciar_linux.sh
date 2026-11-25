#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "============================================================================"
echo "  MuniCertificados — Sistema Institucional de Emisión de Certificados"
echo "  Municipalidad de San Roque, Corrientes — Área de Modernización y Redes"
echo "============================================================================"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] No se detectó python3 instalado en el sistema."
    echo "En Ubuntu/Debian ejecute: sudo apt update && sudo apt install -y python3 python3-venv python3-tk"
    exit 1
fi

if [ ! -f ".venv/bin/python" ]; then
    echo "[1/3] Creando entorno virtual local (.venv)..."
    python3 -m venv .venv
    echo "[2/3] Instalando dependencias desde requirements.txt..."
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
else
    echo "[1/2] Entorno virtual detectado (.venv). Verificando dependencias..."
    .venv/bin/pip install -q -r requirements.txt
fi

echo "[OK] Iniciando MuniCertificados..."
exec .venv/bin/python main.py

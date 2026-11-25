#!/usr/bin/env bash
# Hata, tanımsız değişken veya boru hattı hatasında başlangıcı durdur.
set -euo pipefail
# Komut başka klasörden çağrılsa da proje kökünden çalış.
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Önce README.md içindeki sanal ortam kurulumunu tamamlayın."
  exit 1
fi
# Sanal ortamdaki Python ile yerel sunucuyu başlat; PORTATLAS_PORT verilmezse 8000 kullanılır.
exec .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port "${PORTATLAS_PORT:-8000}"

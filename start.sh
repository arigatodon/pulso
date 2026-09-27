#!/usr/bin/env bash
# Pulso · Polar H10 — lanzador para Linux y macOS
# Sirve la app en http://localhost:8765 y abre el navegador.
cd "$(dirname "$0")"
PORT="${1:-8765}"
URL="http://localhost:$PORT"

open_browser() {
  if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 &
  elif command -v open >/dev/null 2>&1; then open "$URL"
  else echo "Abre $URL en Chrome o Edge"; fi
}

if command -v python3 >/dev/null 2>&1; then
  echo "Pulso disponible en $URL  (Ctrl+C para detener)"
  (sleep 1; open_browser) &
  exec python3 -m http.server "$PORT" --bind 127.0.0.1
elif command -v python >/dev/null 2>&1; then
  echo "Pulso disponible en $URL  (Ctrl+C para detener)"
  (sleep 1; open_browser) &
  exec python -m http.server "$PORT" --bind 127.0.0.1
else
  echo "No se encontró Python. Abriendo index.html directamente (funciona en Chrome/Edge)."
  URL="file://$(pwd)/index.html"; open_browser
fi

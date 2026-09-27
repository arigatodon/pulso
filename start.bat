@echo off
rem Pulso - Polar H10: lanzador para Windows
rem Sirve la app en http://localhost:8765 y abre el navegador.
cd /d "%~dp0"
set PORT=8765
if not "%~1"=="" set PORT=%~1
where py >NUL 2>NUL && (set PY=py) || (where python >NUL 2>NUL && (set PY=python) || (set PY=))
if "%PY%"=="" (
  echo No se encontro Python. Abriendo index.html directamente ^(funciona en Chrome/Edge^).
  start "" "%~dp0index.html"
  exit /b
)
echo Pulso disponible en http://localhost:%PORT%  (Ctrl+C para detener)
start "" "http://localhost:%PORT%"
%PY% -m http.server %PORT% --bind 127.0.0.1

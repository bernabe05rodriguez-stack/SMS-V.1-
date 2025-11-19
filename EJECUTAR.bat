@echo off
REM Ejecuta la aplicación desde la carpeta actual
cd /d "%~dp0"

echo Iniciando SMS Multi-Perfil...

echo Verificando entorno virtual...
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXEC=.venv\Scripts\python.exe"
    echo Usando Python del entorno virtual.
) else (
    set "PYTHON_EXEC=python"
    echo Usando Python global del sistema.
)

echo Abriendo lanzador...
%PYTHON_EXEC% launcher.py

if errorlevel 1 (
    echo Hubo un error al abrir la aplicacion.
    pause
)

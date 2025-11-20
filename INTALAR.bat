@echo off
REM Prepara el entorno de la aplicacion instalando dependencias necesarias
cd /d "%~dp0"

echo Iniciando instalacion de dependencias...

REM Crear entorno virtual si no existe
if exist ".venv\Scripts\python.exe" (
    echo Entorno virtual detectado. Se reutilizara.
) else (
    echo Creando entorno virtual en .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

set "PYTHON_EXEC=.venv\Scripts\python.exe"
if not exist "%PYTHON_EXEC%" (
    set "PYTHON_EXEC=python"
    echo No se encontro el Python del entorno virtual. Se usara el Python global.
)

echo Actualizando pip...
"%PYTHON_EXEC%" -m pip install --upgrade pip
if errorlevel 1 (
    echo Error al actualizar pip.
    pause
    exit /b 1
)

echo Instalando dependencias desde requirements.txt...
"%PYTHON_EXEC%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Ocurrio un error al instalar las dependencias.
    pause
    exit /b 1
)

echo Instalacion completada.
pause

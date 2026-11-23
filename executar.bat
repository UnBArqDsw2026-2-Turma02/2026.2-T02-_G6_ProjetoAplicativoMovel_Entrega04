@echo off
cd /d "%~dp0"

set "COMANDO_PYTHON=python"
where py >nul 2>nul
if %errorlevel%==0 set "COMANDO_PYTHON=py -3"

%COMANDO_PYTHON% --version >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado. Instale o Python 3.10 ou superior em https://www.python.org/downloads/
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando o ambiente virtual .venv ...
  %COMANDO_PYTHON% -m venv .venv
)

echo Instalando as dependencias ...
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r aplicativo\requirements.txt
if errorlevel 1 (
  echo Nao foi possivel instalar as dependencias. Verifique a conexao com a internet.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -m aplicativo %*
pause

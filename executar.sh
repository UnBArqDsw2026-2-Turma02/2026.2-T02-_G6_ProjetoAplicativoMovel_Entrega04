#!/usr/bin/env sh
set -e
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  comando_python=python3
elif command -v python >/dev/null 2>&1; then
  comando_python=python
else
  echo "Python não encontrado. Instale o Python 3.10 ou superior em https://www.python.org/downloads/"
  exit 1
fi

if [ ! -d .venv ]; then
  echo "Criando o ambiente virtual .venv ..."
  "$comando_python" -m venv .venv
fi

if [ -x .venv/bin/python ]; then
  python_ambiente=.venv/bin/python
else
  python_ambiente=.venv/Scripts/python.exe
fi

echo "Instalando as dependências ..."
"$python_ambiente" -m pip install --quiet --disable-pip-version-check -r aplicativo/requirements.txt

exec "$python_ambiente" -m aplicativo "$@"

#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    python -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo
echo "PyQt4 and the Keysight/Agilent 4294A VISA drivers must be installed on this system."
echo "If PyQt4 is missing, install it with a compatible legacy Python/Qt environment before running the GUI."
echo

python script.py

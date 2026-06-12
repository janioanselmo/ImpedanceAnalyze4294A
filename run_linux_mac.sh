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
echo "PyQt5 and the Keysight/Agilent 4294A VISA drivers must be installed on this system."
echo "Use the simulation checkbox to test discovery without physical hardware when pyvisa-sim is available."
echo

python script.py

@echo off
cd /d %~dp0

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo PyQt5 and the Keysight/Agilent 4294A VISA drivers must be installed on this system.
echo Use the simulation checkbox to test discovery without physical hardware when pyvisa-sim is available.
echo.

python script.py

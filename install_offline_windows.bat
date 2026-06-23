@echo off
cd /d %~dp0

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --no-index --find-links offline\wheels -r requirements.txt

echo.
echo Offline install complete.
echo If the equipment uses 10.1.1.2, configure this PC Ethernet as 10.1.1.1 / 255.255.255.0.
echo Then test:
echo   python scripts\visa_diagnostic.py --py TCPIP0::10.1.1.2::inst0::INSTR
echo   python scripts\visa_diagnostic.py --py TCPIP0::10.1.1.2::5025::SOCKET
echo   python scripts\visa_diagnostic.py --py TCPIP0::10.1.1.2::gpib0,17::INSTR
echo.

python script.py

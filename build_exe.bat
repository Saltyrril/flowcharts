@echo off
setlocal
cd /d "%~dp0"
echo === Building GostFlow.exe ===

set PY=
where python >nul 2>nul
if not errorlevel 1 set PY=python
if "%PY%"=="" (
  where py >nul 2>nul
  if not errorlevel 1 set PY=py
)
if "%PY%"=="" goto nopython

%PY% -m pip install --upgrade pip pyinstaller pillow
if errorlevel 1 goto pipfail

%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name GostFlow --icon icon.ico GostFlow.pyw
if errorlevel 1 goto buildfail

echo.
echo DONE: dist\GostFlow.exe  (single file, copy it anywhere)
pause
exit /b 0

:nopython
echo Python was not found. Install Python 3.9+ from python.org and tick "Add Python to PATH".
pause
exit /b 1

:pipfail
echo Failed to install dependencies. Check your internet connection.
pause
exit /b 1

:buildfail
echo Build failed. Send the text above to the developer.
pause
exit /b 1

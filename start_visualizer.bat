
@echo off
setlocal
title Poker Simulator

cd /d "%~dp0"

echo ========================================
echo          POKER SIMULATOR START
echo ========================================
echo.

where py >nul 2>&1
if errorlevel 1 goto USE_PYTHON

echo Python Launcher found.
echo.

echo Installing required libraries...
py -3 -m pip install --disable-pip-version-check streamlit pillow opencv-python ultralytics numpy

if errorlevel 1 goto ERROR

echo.
echo ========================================
echo       STARTING POKER SIMULATOR
echo ========================================
echo.

py -3 -m streamlit run "%~dp0Final_project.py" --server.address 127.0.0.1 --server.port 8501

goto END


:USE_PYTHON

echo Python Launcher not found.
echo Trying python command...
echo.

python -m pip install --disable-pip-version-check streamlit pillow opencv-python ultralytics numpy

if errorlevel 1 goto ERROR

echo.
echo ========================================
echo       STARTING POKER SIMULATOR
echo ========================================
echo.

python -m streamlit run "%~dp0Final_project.py" --server.address 127.0.0.1 --server.port 8501

goto END


:ERROR

echo.
echo ========================================
echo              ERROR
echo ========================================
echo.
echo Could not prepare Python or required libraries.
echo.
echo Please check:
echo 1. Python 3 is installed.
echo 2. Python is added to PATH.
echo 3. Internet connection is available.
echo.

goto END


:END

echo.
echo ========================================
echo       SERVER PROCESS ENDED
echo ========================================
echo.
pause


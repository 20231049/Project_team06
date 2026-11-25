@echo off
setlocal
title Poker Simulator

cd /d "%~dp0"

echo ========================================
echo          POKER SIMULATOR START
echo ========================================
echo.

set "ANACONDA_PY=C:\Users\user\anaconda3\python.exe"

if not exist "%ANACONDA_PY%" goto USE_PYTHON

echo Using Anaconda Python: %ANACONDA_PY%
echo.

echo Installing required libraries...
"%ANACONDA_PY%" -m pip install --disable-pip-version-check streamlit pillow opencv-python ultralytics "numpy<2.0"
if errorlevel 1 goto ERROR

echo.
echo ========================================
echo       STARTING POKER SIMULATOR
echo ========================================
echo.

"%ANACONDA_PY%" -m streamlit run "%~dp0Final_project.py" --server.address 127.0.0.1 --server.port 8501

goto END


:USE_PYTHON

echo Anaconda Python not found.
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
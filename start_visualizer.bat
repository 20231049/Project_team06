@echo off
setlocal
title Poker Simulator

cd /d "%~dp0"

echo ========================================
echo       POKER SIMULATOR START
echo ========================================
echo.

where py >nul 2>&1
if errorlevel 1 goto USE_PYTHON

echo Python Launcher found.
py -3 -m pip install --disable-pip-version-check streamlit pillow
if errorlevel 1 goto ERROR
py -3 -m streamlit run "%~dp0app.py" --server.address 127.0.0.1 --server.port 8501
goto END

:USE_PYTHON
echo Trying python command...
python -m pip install --disable-pip-version-check streamlit pillow
if errorlevel 1 goto ERROR
python -m streamlit run "%~dp0app.py" --server.address 127.0.0.1 --server.port 8501
goto END

:ERROR
echo.
echo Could not prepare Python or Streamlit.
echo Check that Python 3 is installed and added to PATH.

:END
echo.
echo Server process ended.
pause

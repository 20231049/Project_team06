@echo off
setlocal
title Real-time Poker Simulator

cd /d "%~dp0"

echo ========================================
echo       REAL-TIME POKER SIMULATOR
echo ========================================
echo.

set "ANACONDA_PY=C:\Users\user\anaconda3\python.exe"

if not exist "%ANACONDA_PY%" goto USE_PYTHON

echo Using Anaconda Python: %ANACONDA_PY%
echo.

"%ANACONDA_PY%" -m pip install --disable-pip-version-check streamlit pillow opencv-python ultralytics "numpy<2.0" "pyarrow<18" streamlit-webrtc av streamlit-autorefresh

if errorlevel 1 goto ERROR

echo.
echo Starting Poker Simulator...
echo.

"%ANACONDA_PY%" -m streamlit run "%~dp0Final_project.py" --server.address 127.0.0.1 --server.port 8501

goto END

:USE_PYTHON

echo Anaconda Python not found. Trying python command...
echo.

python -m pip install --disable-pip-version-check streamlit pillow opencv-python ultralytics "numpy<2.0" "pyarrow<18" streamlit-webrtc av streamlit-autorefresh

if errorlevel 1 goto ERROR

echo.
echo Starting Poker Simulator...
echo.

python -m streamlit run "%~dp0Final_project.py" --server.address 127.0.0.1 --server.port 8501

goto END

:ERROR

echo.
echo Could not install required libraries.
echo Check Python 3 and internet connection.
echo.

:END

echo.
echo Server process ended.
pause
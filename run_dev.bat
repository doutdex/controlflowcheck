@echo off
REM Development launcher - edit the conda env name if needed
REM Double-click to run the app in the project root environment
REM Replace cv311 with your conda env name if different
call conda activate cv311
poetry run python src/main.py

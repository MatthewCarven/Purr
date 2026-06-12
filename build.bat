@echo off
REM build.bat — build a standalone purr.exe with PyInstaller.
REM The exe accepts all of purr's command-line parameters
REM (FILE, -e/--effect, -l/--list, -p/--page-lines, -f/--frame-rate).
setlocal
cd /d "%~dp0"

echo Checking dependencies...
python -m pip show terminaltexteffects >nul 2>nul || (
    echo Installing terminaltexteffects...
    python -m pip install terminaltexteffects || goto :fail
)
python -m PyInstaller --version >nul 2>nul || (
    echo Installing PyInstaller...
    python -m pip install pyinstaller || goto :fail
)

echo Building purr.exe...
REM --collect-submodules is required: purr loads effect modules dynamically
REM (importlib), which PyInstaller's static analysis cannot see.
python -m PyInstaller --onefile --console --name purr ^
    --collect-submodules terminaltexteffects ^
    --noconfirm --clean purr.py || goto :fail

echo.
echo Build complete: dist\purr.exe
echo Try it:  dist\purr.exe --list
echo          dist\purr.exe README.md -e decrypt
exit /b 0

:fail
echo.
echo Build failed.
exit /b 1

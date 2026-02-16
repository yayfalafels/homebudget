@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%\..\.."

pushd "%ROOT_DIR%" >nul

if not exist ".dev\env\Scripts\activate" (
  echo ERROR: .dev\env not found.
  echo Run the design phase setup to create the scaffolding environment.
  popd >nul
  exit /b 1
)

if not exist "requirements.txt" (
  echo ERROR: requirements.txt not found in %ROOT_DIR%.
  echo Ensure you run this script from the repository.
  popd >nul
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: python not found in PATH.
  echo Install Python 3.10 or higher and retry.
  popd >nul
  exit /b 1
)

python -c "import sys; print(sys.version); raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
  echo ERROR: Python 3.10 or higher is required.
  popd >nul
  exit /b 1
)

if exist "env\Scripts\activate" (
  echo Main environment already exists. Skipping creation.
) else (
  echo Creating main environment at env
  python -m venv env
  if errorlevel 1 (
    echo ERROR: failed to create env.
    echo Check that Python is installed and retry.
    popd >nul
    exit /b 1
  )
)

call "env\Scripts\activate"
if errorlevel 1 (
  echo ERROR: failed to activate env.
  echo Try running: env\Scripts\activate
  popd >nul
  exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 (
  echo ERROR: failed to upgrade pip.
  popd >nul
  exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: failed to install dependencies from requirements.txt.
  popd >nul
  exit /b 1
)

python -m pip install build setuptools wheel
if errorlevel 1 (
  echo ERROR: failed to install build tools.
  popd >nul
  exit /b 1
)

echo Setup complete.

popd >nul
exit /b 0

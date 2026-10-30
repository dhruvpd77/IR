@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo Creating the Python environment...
  py -m venv venv
  call venv\Scripts\python -m pip install -r requirements.txt
)
call venv\Scripts\python manage.py migrate
call venv\Scripts\python manage.py seed_demo
echo.
echo This PC:       http://127.0.0.1:8000/
echo TV on the LAN: http://THIS-PC-IP:8000/   then open Live board and full screen
echo.
echo Super Admin    superadmin     IR@Super2026
echo Admin          admin          IR@Admin2026
echo Employee       employee       IR@User2026
echo.
call venv\Scripts\python manage.py runserver 0.0.0.0:8000

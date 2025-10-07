@echo off
cd /d "%~dp0"
set /p MSG=Commit message: 
git add .
git commit -m "%MSG%" || echo No changes to commit
git pull --rebase
git push
pause

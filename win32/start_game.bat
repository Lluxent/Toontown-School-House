@echo off
title Toontown Online - Game Client
cd..

set TTOFF_LOGIN_TOKEN=dev
python\ppython.exe -m toontown.launcher.TTOffQuickStartLauncher
pause

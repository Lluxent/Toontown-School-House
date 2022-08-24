@echo off
title Toontown Online - Developer Mini-Server Launcher
cd..

echo Toontown Online Developer Mini-Server Launcher
echo.
echo NOTE: Make sure that "mini-server" is enabled in your settings.json!
echo.

set /P TTOFF_LOGIN_TOKEN="Username (default: dev): " || ^
set TTOFF_LOGIN_TOKEN=dev

set /P TTOFF_GAME_SERVER="Game Server (default: 127.0.0.1): " || ^
set TTOFF_GAME_SERVER=127.0.0.1

python\ppython.exe -m toontown.launcher.TTOffQuickStartLauncher
pause

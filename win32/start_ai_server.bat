@echo off
title Toontown Online - AI (District) Server
cd..

:main
python\ppython.exe -m toontown.ai.AIStart --base-channel 401000000 ^
               --max-channels 999999 --stateserver 4002 ^
               --astron-ip 127.0.0.1:7199 --eventlogger-ip 127.0.0.1:7197 ^
               --district-name "Toon Valley"
goto main

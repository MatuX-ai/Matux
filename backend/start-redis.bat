@echo off
cd /d "G:\iMato\backend\redis"
echo Starting Redis Server...
redis-server.exe redis.windows.conf
pause
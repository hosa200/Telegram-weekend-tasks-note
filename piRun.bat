@echo off
setlocal

echo ===================================================
echo       Raspberry Pi Telegram Agent Deployer
echo ===================================================
echo.

set /p PI_HOST="Enter Raspberry Pi IP Address or Hostname (e.g., 192.168.1.50): "
set /p PI_USER="Enter Raspberry Pi Username (press Enter for default 'pi'): "
if "%PI_USER%"=="" set PI_USER=pi

set /p PI_PASS="Enter Raspberry Pi Password (for sudo): "

set PI_DIR=/home/%PI_USER%/weekend_agent
set LOCAL_DIR=%~dp0

echo.
echo [1/6] Checking remaining SD card disk space on the Pi...
ssh %PI_USER%@%PI_HOST% "df -h /"

echo.
echo [2/6] Connecting to %PI_HOST% and preparing directory...
ssh %PI_USER%@%PI_HOST% "mkdir -p %PI_DIR%"

echo [3/6] Copying files to Raspberry Pi via SCP...
scp "%LOCAL_DIR%agent.py" %PI_USER%@%PI_HOST%:%PI_DIR%/
scp "%LOCAL_DIR%tasks.json" %PI_USER%@%PI_HOST%:%PI_DIR%/

echo [4/6] Installing lightweight dependencies (faster-whisper) on the Pi...
ssh %PI_USER%@%PI_HOST% "cd %PI_DIR% && python3 -m venv .venv && source .venv/bin/activate && pip install --upgrade pip && pip install faster-whisper python-telegram-bot"

echo [5/6] Setting up systemd background service on the Pi...
ssh %PI_USER%@%PI_HOST% "echo %PI_PASS% | sudo -S sh -c 'echo -e \"[Unit]\nDescription=Telegram Weekend Task Agent\nAfter=network.target\n\n[Service]\nUser=%PI_USER%\nWorkingDirectory=%PI_DIR%\nExecStart=%PI_DIR%/.venv/bin/python agent.py\nRestart=always\nRestartSec=10\n\n[Install]\nWantedBy=multi-user.target\" > /etc/systemd/system/telegram-agent.service'"

echo [6/6] Enabling and restarting the background service...
ssh %PI_USER%@%PI_HOST% "echo %PI_PASS% | sudo -S systemctl daemon-reload && echo %PI_PASS% | sudo -S systemctl enable telegram-agent.service && echo %PI_PASS% | sudo -S systemctl restart telegram-agent.service"

echo.
echo ===================================================
echo  Deployment complete! Your bot is live on the Pi.
echo ===================================================
pause
@echo off
REM Convert.id — Windows CMD Batch Installer Wrapper
REM Runs PowerShell installer seamlessly from Command Prompt (CMD)

powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/muhmdathalla/convert.id/main/install.ps1 | iex"

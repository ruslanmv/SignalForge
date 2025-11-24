@echo off
chcp 65001 >nul

echo ╔════════════════════════════════════════╗
echo ║  SignalForge MCP Server (HTTP Mode)    ║
echo ╚════════════════════════════════════════╝
echo.

REM Check virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo ❌ [Error] Virtual environment not found
    echo Please run setup-windows.bat or setup-windows-en.bat first to deploy.
    echo.
    pause
    exit /b 1
)

echo [Mode] HTTP (Suitable for remote access)
echo [Address] http://localhost:3333/mcp
echo [Tip] Press Ctrl+C to stop the service
echo.

uv run python -m mcp_server.server --transport http --host 0.0.0.0 --port 3333

pause
@echo off
echo Iniciando Servidor de Inventario...
cd backend
python validate_server.py
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Falha na validacao do servidor. Verifique os erros acima.
    pause
    exit /b %ERRORLEVEL%
)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause

@echo off
echo Instalando PyInstaller...
echo Instalando dependencias...
pip install -r agent_requirements.txt

echo Compilando Agente...
python -m PyInstaller --onefile --name "InventarioAgent" agent/inventory_agent.py

echo.
echo [SUCESSO] O executavel foi criado na pasta 'dist'.
pause

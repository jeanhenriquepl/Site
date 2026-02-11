@echo off
echo ==========================================
echo       RESETANDO BANCO DE DADOS
echo ==========================================
echo.
echo Por favor, certifique-se de que o servidor (janela do Python/CMD) esta FECHADO.
echo Se o servidor estiver rodando, este script falhara.
echo.
pause

if exist "backend\inventory.db" (
    del "backend\inventory.db"
    if exist "backend\inventory.db" (
        echo [ERRO] Nao foi possivel deletar o arquivo. O servidor ainda esta rodando?
        echo Tente fechar todas as janelas do Python e tente novamente.
        pause
        exit /b 1
    ) else (
        echo [SUCESSO] Banco de dados antigo removido via backend/inventory.db.
    )
) else (
    echo Arquivo backend\inventory.db nao encontrado (ja deletado?).
)

if exist "inventory.db" (
    del "inventory.db"
    echo [SUCESSO] Banco de dados antigo removido via inventory.db.
)

echo.
echo Agora voce pode iniciar o servidor novamente (start_server.bat).
echo O banco de dados sera recriado automaticamente com a nova estrutura.
echo.
pause

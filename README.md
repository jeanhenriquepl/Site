# Sistema de Inventário de TI

Sistema completo para gerenciamento de ativos de TI, monitoramento de hardware e controle de serviços remotos.

## 🚀 Funcionalidades
*   **Dashboard Web**: Visualização de todas as máquinas, status (Online/Offline) e alertas.
*   **Monitoramento em Tempo Real**: CPU, RAM, Disco.
*   **Inventário Automático**: Hardware (Processador, Serial) e Software instalado.
*   **Controle Remoto**: Iniciar, Parar e Reiniciar serviços do Windows remotamente.
*   **Agente Leve**: Script em Python (ou .exe) que roda nas estações.

## 🛠️ Tecnologias
*   **Backend**: Python (FastAPI), SQLModel (SQLite).
*   **Frontend**: HTML, CSS, JavaScript (Puro).
*   **Agente**: Python (psutil, wmi, requests).
*   **Deploy**: Pronto para Render.com / Docker.

## 📦 Como Rodar Localmente
1.  Instale as dependências: `pip install -r requirements.txt`
2.  Inicie o servidor: `start_server.bat`
3.  Acesse: `http://localhost:8000`

## ☁️ Como Rodar no Render (Produção)
Este projeto já possui `Procfile` e `requirements.txt` configurados.
1.  Conecte este repositório no Render.
2.  Build Command: `pip install -r requirements.txt`
3.  Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

---
Desenvolvido para gestão eficiente de parques tecnológicos.

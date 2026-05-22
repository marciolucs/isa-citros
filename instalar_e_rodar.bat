@echo off
echo ================================================
echo  ISA - Sistema de Inspecao Fitossanitaria Citros
echo ================================================
echo.

:: Verifica Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo Instale Python em: https://www.python.org/downloads/
    echo Marque "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

echo [1/3] Python encontrado. Instalando dependencias...
python -m pip install streamlit pandas reportlab plotly pillow --quiet

if %errorlevel% neq 0 (
    echo ERRO ao instalar dependencias. Verifique sua conexao com a internet.
    pause
    exit /b 1
)

echo [2/3] Dependencias instaladas com sucesso!
echo [3/3] Iniciando o sistema...
echo.
echo Acesse no navegador: http://localhost:8501
echo Para encerrar: pressione CTRL+C nesta janela
echo.

cd /d "%~dp0"
python -m streamlit run app.py

pause

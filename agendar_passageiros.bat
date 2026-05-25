@echo off
:: agendar_passageiros.bat
:: Registra uma tarefa no Agendador de Tarefas do Windows
:: para rodar atualizar_passageiros.py a cada 1 hora.
:: Execute este arquivo UMA VEZ como Administrador.

set PASTA=%~dp0
set PYTHON=python
set SCRIPT=%PASTA%atualizar_passageiros.py

echo Registrando tarefa "PassageirosUpdate"...

schtasks /create /tn "PassageirosUpdate" ^
  /tr "\"%PYTHON%\" \"%SCRIPT%\"" ^
  /sc HOURLY ^
  /mo 1 ^
  /st 00:00 ^
  /ru "%USERNAME%" ^
  /f

if %errorlevel%==0 (
    echo.
    echo OK — Tarefa registrada com sucesso!
    echo A planilha sera atualizada a cada 1 hora automaticamente.
    echo.
    echo Para ver a tarefa:   Agendador de Tarefas ^> PassageirosUpdate
    echo Para remover:        schtasks /delete /tn "PassageirosUpdate" /f
) else (
    echo.
    echo ERRO ao registrar tarefa. Tente executar como Administrador.
)

pause

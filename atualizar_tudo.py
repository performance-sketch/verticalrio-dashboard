"""
atualizar_tudo.py
=================
Atualiza todos os dados do dashboard de uma vez.
Execute: python atualizar_tudo.py

Ordem:
  1. Meta Ads (atualizar_meta.py)
  2. Google Ads (atualizar_google.py)
  3. Rezdy (atualizar_dados.py)
"""

import subprocess
import sys
from datetime import datetime

def rodar(script):
    print(f"\n{'='*55}")
    print(f"  Rodando {script}...")
    print(f"{'='*55}")
    result = subprocess.run([sys.executable, script], capture_output=False)
    if result.returncode != 0:
        print(f"\n  [AVISO] {script} encerrou com erro (codigo {result.returncode})")
    return result.returncode == 0

inicio = datetime.now()
print(f"\n{'='*55}")
print(f"  ATUALIZANDO DASHBOARD — {inicio.strftime('%d/%m/%Y %H:%M')}")
print(f"{'='*55}")

ok_meta   = rodar("atualizar_meta.py")
ok_google = rodar("atualizar_google.py")
ok_rezdy  = rodar("atualizar_dados.py")

fim = datetime.now()
duracao = (fim - inicio).seconds

print(f"\n{'='*55}")
print(f"  RESUMO")
print(f"{'='*55}")
print(f"  Meta Ads:   {'OK' if ok_meta   else 'ERRO — verifique token/conta'}")
print(f"  Google Ads: {'OK' if ok_google else 'ERRO — verifique credenciais'}")
print(f"  Rezdy:      {'OK' if ok_rezdy  else 'ERRO — verifique chave API'}")
print(f"  Duracao:    {duracao}s")
print(f"\n  Abra: dashboard_completo.html\n")

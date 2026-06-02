"""
atualizar_respondio.py
======================
Busca dados do Respond.io via API v2 e atualiza o index.html.

ENDPOINT FUNCIONAL CONFIRMADO:
  POST https://api.respond.io/v2/contact/list
  Body: {"search":"","filter":{"$and":[]},"timezone":"America/Sao_Paulo","limit":100}
  Paginacao: GET pagination.next com header Authorization

Metricas extraidas dos contatos:
  - Funil de ciclo de vida (lifecycle)
  - Tags por idioma/categoria
  - Distribuicao por agente (assignee)
  - Status aberto/fechado
  - Contatos por pais (countryCode)
  - Novos contatos por dia (created_at)

Execute: python atualizar_respondio.py
"""

import requests
import json
import re
import sys
import time
from datetime import datetime, timedelta
from collections import defaultdict

# ─── CONFIGURACAO ─────────────────────────────────────────────────────────────
ACCESS_TOKEN  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Mjg0NDMsInNwYWNlSWQiOjI5ODE4OCwib3JnSWQiOjI5NDM3NiwidHlwZSI6ImFwaSIsImlhdCI6MTc3OTQ3MTc0NX0.kVCK6O588AHIdCPTESLEBFxWvX0LQrcGB2Yj6uzmqB0"
ARQUIVO_DASH  = "index.html"
BASE_URL      = "https://api.respond.io/v2"
TIMEZONE      = "America/Sao_Paulo"
LIMITE_PAGINA = 100
MAX_PAGINAS   = 200   # ate 20.000 contatos
# ──────────────────────────────────────────────────────────────────────────────

# Estagio real conforme retornado pela API (ajuste se mudar no Respond.io)
ESTAGIOS_FUNIL = [
    "1. New Lead",
    "2. Negociando",
    "3. Proposta Enviada",
    "4. Fechado",
    "X Parceria",
    "Descarte",
]


def log(msg):
    print(msg, flush=True)


def headers():
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept":        "application/json",
        "Content-Type":  "application/json",
    }


# ─── CONEXAO ──────────────────────────────────────────────────────────────────

def testar_conexao():
    log("Testando conexao com Respond.io...")
    body = {"search": "", "filter": {"$and": []}, "timezone": TIMEZONE, "limit": 1}
    try:
        r = requests.post(f"{BASE_URL}/contact/list", headers=headers(), json=body, timeout=15)
        if r.ok:
            log("  Token valido — API respondeu OK")
            return True
        elif r.status_code == 401:
            log("  ERRO 401: Token invalido ou expirado.")
            log("  Solucao: Regenere em app.respond.io >> Settings >> Developer API")
            return False
        elif r.status_code == 403:
            log("  ERRO 403: Sem permissao. Verifique plano (Growth Plan+)")
            return False
        else:
            log(f"  ERRO {r.status_code}: {r.text[:200]}")
            return False
    except Exception as e:
        log(f"  ERRO de conexao: {e}")
        return False


# ─── BUSCA DE CONTATOS (endpoint confirmado) ──────────────────────────────────

def buscar_todos_contatos():
    """
    Pagina por todos os contatos via:
      1a pagina: POST /v2/contact/list  (body com filter $and)
      proximas:  GET  pagination.next   (URL completa retornada pela API)
    """
    log("Buscando contatos...")
    todos = []
    pagina = 0

    # 1a requisicao — POST
    body = {
        "search":   "",
        "filter":   {"$and": []},
        "timezone": TIMEZONE,
        "limit":    LIMITE_PAGINA,
    }
    r = requests.post(f"{BASE_URL}/contact/list", headers=headers(), json=body, timeout=30)
    if not r.ok:
        log(f"  ERRO {r.status_code}: {r.text[:200]}")
        return []

    dado = r.json()
    itens = dado.get("items") or []
    todos.extend(itens)
    prox_url = (dado.get("pagination") or {}).get("next")
    pagina += 1

    if pagina % 10 == 0 or len(todos) <= LIMITE_PAGINA:
        log(f"  {len(todos)} contatos (pagina {pagina})...")

    # Paginas seguintes — GET na URL de paginacao
    while prox_url and pagina < MAX_PAGINAS:
        time.sleep(0.1)
        r = requests.get(prox_url, headers=headers(), timeout=30)
        if not r.ok:
            log(f"  AVISO paginacao {r.status_code}: parando")
            break
        dado  = r.json()
        itens = dado.get("items") or []
        if not itens:
            break
        todos.extend(itens)
        prox_url = (dado.get("pagination") or {}).get("next")
        pagina += 1
        if pagina % 10 == 0:
            log(f"  {len(todos)} contatos (pagina {pagina})...")

    log(f"  Total: {len(todos)} contatos em {pagina} paginas")
    return todos


# ─── PROCESSAMENTO ────────────────────────────────────────────────────────────

def processar_ciclo_de_vida(contatos):
    contagem = defaultdict(int)
    for c in contatos:
        estagio = c.get("lifecycle") or "Sem Estagio"
        contagem[str(estagio).strip()] += 1

    # Funil ordenado
    funil = []
    for nome in ESTAGIOS_FUNIL:
        funil.append({"estagio": nome, "total": contagem.get(nome, 0)})

    # Estagios nao mapeados
    for k, v in sorted(contagem.items(), key=lambda x: -x[1]):
        if k not in ESTAGIOS_FUNIL and k != "Sem Estagio":
            funil.append({"estagio": k, "total": v, "outro": True})

    funil.append({"estagio": "Sem Estagio", "total": contagem.get("Sem Estagio", 0), "outro": True})
    return funil, dict(contagem)


def processar_tags(contatos):
    contagem = defaultdict(int)
    for c in contatos:
        for tag in (c.get("tags") or []):
            nome = tag.strip() if isinstance(tag, str) else str(tag)
            if nome:
                contagem[nome] += 1
    return [{"nome": k, "total": v}
            for k, v in sorted(contagem.items(), key=lambda x: -x[1])]


def processar_agentes(contatos):
    agentes = defaultdict(lambda: {"abertos": 0, "fechados": 0, "total": 0})
    for c in contatos:
        a = c.get("assignee")
        if not a:
            continue
        nome = (
            f"{a.get('firstName', '')} {a.get('lastName', '')}".strip()
            or a.get("email", "")
            or f"Agente {a.get('id','?')}"
        )
        agentes[nome]["total"] += 1
        if c.get("status") == "open":
            agentes[nome]["abertos"] += 1
        else:
            agentes[nome]["fechados"] += 1

    return [{"nome": k, **v}
            for k, v in sorted(agentes.items(), key=lambda x: -x[1]["total"])]


def processar_paises(contatos):
    contagem = defaultdict(int)
    for c in contatos:
        pais = c.get("countryCode") or "??"
        contagem[pais] += 1
    return dict(sorted(contagem.items(), key=lambda x: -x[1]))


def processar_novos_por_dia(contatos, dias=90):
    por_dia = defaultdict(int)
    corte   = datetime.now() - timedelta(days=dias)
    for c in contatos:
        ts = c.get("created_at")
        if not ts:
            continue
        try:
            dt = datetime.fromtimestamp(int(ts))
            if dt >= corte:
                por_dia[dt.strftime("%Y-%m-%d")] += 1
        except Exception:
            pass
    return dict(sorted(por_dia.items()))


def processar_status(contatos):
    contagem = defaultdict(int)
    for c in contatos:
        contagem[c.get("status") or "open"] += 1
    return dict(contagem)


# ─── ATUALIZAR HTML ────────────────────────────────────────────────────────────

def atualizar_html(dados):
    with open(ARQUIVO_DASH, encoding="utf-8") as f:
        html = f.read()

    novo_json = json.dumps(dados, ensure_ascii=False, indent=2)
    padrao    = r"(const DADOS_RESPONDIO\s*=\s*)(\{[\s\S]*?\})(\s*;)"
    novo_html, n = re.subn(padrao, lambda m: m.group(1) + novo_json + m.group(3), html)
    if n == 0:
        log("  AVISO: 'DADOS_RESPONDIO' nao encontrado no HTML — criando arquivo separado.")
        with open("respondio_dados.json", "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        log("  Dados salvos em respondio_dados.json")
        return

    with open(ARQUIVO_DASH, "w", encoding="utf-8") as f:
        f.write(novo_html)
    log(f"  DADOS_RESPONDIO atualizado ({len(novo_html):,} chars)")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    log(f"\n=== Respond.io -- {datetime.now().strftime('%d/%m/%Y %H:%M')} ===\n")

    if not testar_conexao():
        log("\nSolucao de problemas:")
        log("  1. Acesse app.respond.io >> Settings >> Developer API")
        log("  2. Clique em 'Generate API Key'")
        log("  3. Cole o novo token em ACCESS_TOKEN neste arquivo")
        sys.exit(1)

    log("")
    contatos = buscar_todos_contatos()

    if not contatos:
        log("Nenhum contato encontrado. Verifique token e plano.")
        sys.exit(1)

    log("\nProcessando...")
    funil, contagem_estagios = processar_ciclo_de_vida(contatos)
    tags          = processar_tags(contatos)
    agentes       = processar_agentes(contatos)
    paises        = processar_paises(contatos)
    novos_por_dia = processar_novos_por_dia(contatos, dias=90)
    status        = processar_status(contatos)

    resultado = {
        "totalContatos":    len(contatos),
        "cicloDaVida":      funil,
        "contagemEstagios": contagem_estagios,
        "tags":             tags,
        "agentes":          agentes,
        "paises":           paises,
        "novosPorDia":      novos_por_dia,
        "status":           status,
        "dataAtualizacao":  datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

    # Resumo terminal
    log(f"\n  Total contatos:  {len(contatos):,}")
    log(f"  Abertos:         {status.get('open', 0):,}")
    log(f"  Fechados:        {status.get('closed', 0):,}")
    log(f"\n  Funil de ciclo de vida:")
    for e in funil:
        if e["total"] > 0:
            log(f"    {e['estagio']:<28} {e['total']:>5}")
    log(f"\n  Top agentes:")
    for a in agentes[:5]:
        log(f"    {a['nome']:<30} {a['total']:>5} contatos")
    log(f"\n  Top tags:")
    for t in tags[:5]:
        log(f"    {t['nome']:<25} {t['total']:>5}")
    log(f"\n  Top paises:")
    for p, v in list(paises.items())[:5]:
        log(f"    {p:<10} {v:>5}")

    log(f"\nAtualizando {ARQUIVO_DASH}...")
    atualizar_html(resultado)
    log("\nRespond.io atualizado com sucesso!")


if __name__ == "__main__":
    main()

"""
atualizar_linktree.py
=====================
Busca cliques e analytics do Linktree e atualiza DADOS_LINKTREE no index.html.

Configure seu usuario e senha abaixo, depois execute:
    python atualizar_linktree.py

O Linktree usa autenticação JWT interna. Se a API mudar, ajuste as URLs.
"""

import requests
import json
import re
import time
import sys
from datetime import datetime

# ─── CONFIGURACAO ─────────────────────────────────────────────────────────────
LINKTREE_EMAIL    = ""     # seu e-mail de login no Linktree
LINKTREE_PASSWORD = ""     # sua senha do Linktree
ARQUIVO_DASHBOARD = "index.html"
# ──────────────────────────────────────────────────────────────────────────────

HEADERS_BASE = {
    "Content-Type":  "application/json",
    "Accept":        "application/json",
    "Origin":        "https://linktr.ee",
    "Referer":       "https://linktr.ee/",
    "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def login():
    """Autentica no Linktree e retorna o token JWT."""
    url  = "https://linktr.ee/api/admin/login"
    body = {"username": LINKTREE_EMAIL, "password": LINKTREE_PASSWORD}
    r = requests.post(url, json=body, headers=HEADERS_BASE, timeout=20)
    if not r.ok:
        raise RuntimeError(f"Login falhou ({r.status_code}): {r.text[:300]}")
    data  = r.json()
    token = data.get("token") or data.get("access_token") or (data.get("data") or {}).get("token")
    if not token:
        raise RuntimeError(f"Token nao encontrado na resposta: {list(data.keys())}")
    return token


def buscar_analytics(token):
    """Busca dados de analytics do perfil."""
    hdrs = {**HEADERS_BASE, "Authorization": f"Bearer {token}"}

    # Perfil basico
    r1 = requests.get("https://linktr.ee/api/admin/links", headers=hdrs, timeout=20)
    links_data = r1.json() if r1.ok else {}

    # Analytics de cliques
    r2 = requests.get(
        "https://linktr.ee/api/admin/analytics",
        headers=hdrs, params={"timeRange": "30d"}, timeout=20,
    )
    analytics = r2.json() if r2.ok else {}

    # Tentar GraphQL como fallback
    if not analytics and not links_data:
        gql_url = "https://linktr.ee/graphql"
        payload = {
            "query": """
            query Analytics($dateRange: DateRange) {
              analytics(dateRange: $dateRange) {
                profileViews
                uniqueViews
                totalClicks
                clickThroughRate
                links { title url clicks }
              }
            }""",
            "variables": {"dateRange": "last30Days"},
        }
        r3 = requests.post(gql_url, json=payload, headers=hdrs, timeout=20)
        if r3.ok:
            analytics = r3.json().get("data", {}).get("analytics", {})

    return links_data, analytics


def processar(links_data, analytics):
    """Extrai as métricas relevantes para o dashboard."""
    resultado = {
        "totalCliques":  0,
        "visualizacoes": 0,
        "ctr":           0.0,
        "links":         [],
        "dataAtualizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

    # Se veio de analytics direto
    if isinstance(analytics, dict):
        resultado["totalCliques"]  = analytics.get("totalClicks") or analytics.get("clicks") or 0
        resultado["visualizacoes"] = analytics.get("profileViews") or analytics.get("uniqueViews") or 0
        ctr = analytics.get("clickThroughRate") or analytics.get("ctr") or 0
        resultado["ctr"] = round(float(ctr), 1)

        raw_links = analytics.get("links") or []
        for lk in raw_links:
            resultado["links"].append({
                "titulo":  lk.get("title") or lk.get("name") or "—",
                "url":     lk.get("url") or lk.get("href") or "",
                "cliques": int(lk.get("clicks") or lk.get("click_count") or 0),
            })

    # Se veio de links_data (lista de links com click_count)
    if isinstance(links_data, list):
        for lk in links_data:
            cliques = int(lk.get("click_count") or lk.get("clicks") or 0)
            resultado["links"].append({
                "titulo":  lk.get("title") or "—",
                "url":     lk.get("url") or "",
                "cliques": cliques,
            })
            resultado["totalCliques"] += cliques
    elif isinstance(links_data, dict):
        for lk in (links_data.get("links") or links_data.get("data") or []):
            cliques = int(lk.get("click_count") or lk.get("clicks") or 0)
            resultado["links"].append({
                "titulo":  lk.get("title") or "—",
                "url":     lk.get("url") or "",
                "cliques": cliques,
            })
            resultado["totalCliques"] += cliques

    resultado["links"].sort(key=lambda x: -x["cliques"])
    return resultado


def atualizar_html(dados):
    novo_json = json.dumps(dados, ensure_ascii=False, indent=2)
    with open(ARQUIVO_DASHBOARD, "r", encoding="utf-8") as f:
        html = f.read()

    padrao = r"(const DADOS_LINKTREE\s*=\s*)(\{[\s\S]*?\})(\s*;)"
    novo_html, n = re.subn(
        padrao,
        lambda m: m.group(1) + novo_json + m.group(3),
        html,
    )
    if n == 0:
        print("  [AVISO] DADOS_LINKTREE nao encontrado no HTML — verifique o dashboard")
        return False

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    novo_html = re.sub(
        r'(id="dataLinktree">)[^<]*(</span>)',
        rf'\g<1>{agora}\g<2>',
        novo_html,
    )
    with open(ARQUIVO_DASHBOARD, "w", encoding="utf-8") as f:
        f.write(novo_html)
    return True


def executar():
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"\n=== Atualizando Linktree -- {agora} ===\n")

    if not LINKTREE_EMAIL or not LINKTREE_PASSWORD:
        print("  ATENCAO: Configure LINKTREE_EMAIL e LINKTREE_PASSWORD neste arquivo.")
        return None

    print("Autenticando no Linktree...")
    token = login()
    print("  Token obtido.")

    print("Buscando analytics...")
    links_data, analytics = buscar_analytics(token)

    print("Processando dados...")
    dados = processar(links_data, analytics)

    print(f"  Total cliques: {dados['totalCliques']:,}")
    print(f"  Visualizacoes: {dados['visualizacoes']:,}")
    print(f"  Links:         {len(dados['links'])}")

    print(f"\nAtualizando {ARQUIVO_DASHBOARD}...")
    if atualizar_html(dados):
        print("  OK — Dashboard atualizado!")
    else:
        print("  ERRO — Constante DADOS_LINKTREE nao encontrada")

    return dados


def main():
    loop = "--loop" in sys.argv
    if loop:
        intervalo = 3600
        print(f"Modo loop: atualizando a cada {intervalo//3600}h")
        while True:
            try:
                executar()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"  ERRO: {e}")
            print(f"\nProxima atualizacao em 1h...")
            time.sleep(intervalo)
    else:
        executar()


if __name__ == "__main__":
    main()

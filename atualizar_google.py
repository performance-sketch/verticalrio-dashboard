"""
atualizar_google.py
===================
Busca dados reais do Google Ads API e atualiza o index.html.
Execute: python atualizar_google.py

─── REQUISITOS ──────────────────────────────────────────────────────────────
  pip install google-ads

─── COMO OBTER CREDENCIAIS ──────────────────────────────────────────────────
1. DEVELOPER TOKEN
   - Google Ads (conta MCC ou principal) → Ferramentas → API Center
   - Solicite acesso de producao (ou use o token de teste para testes)

2. OAUTH2 (CLIENT_ID + CLIENT_SECRET + REFRESH_TOKEN)
   a. Google Cloud Console (console.cloud.google.com)
   b. Crie um projeto → Ative "Google Ads API"
   c. Credenciais → Criar credenciais → ID do cliente OAuth (tipo: App para computador)
   d. Baixe o JSON e rode o script abaixo UMA VEZ para gerar o refresh_token:
      python gerar_token_google.py
   e. Cole os valores abaixo

3. CUSTOMER_ID
   - ID da conta Google Ads sem hifens (ex: 1234567890)
   - Conta MCC: use o ID da conta filha (nao da MCC)
──────────────────────────────────────────────────────────────────────────────
"""

import json
import re
from datetime import datetime

# ─── CONFIGURACAO ─────────────────────────────────────────────────────────────
DEVELOPER_TOKEN = "SEU_DEVELOPER_TOKEN"    # Da API Center do Google Ads
CLIENT_ID       = "SEU_CLIENT_ID"          # Do Google Cloud Console
CLIENT_SECRET   = "SEU_CLIENT_SECRET"
REFRESH_TOKEN   = "SEU_REFRESH_TOKEN"      # Gerado por gerar_token_google.py
CUSTOMER_ID     = "XXXXXXXXXX"             # ID da conta sem hifens
LOGIN_CUSTOMER_ID = ""                     # ID da conta MCC (se houver); senao deixe ""

ARQUIVO_DASH    = "index.html"
DATE_RANGE      = "LAST_30_DAYS"
# Opcoes: LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, THIS_MONTH, LAST_MONTH
# ──────────────────────────────────────────────────────────────────────────────

# Mapa de criterion_id (geo) → nome do pais
PAISES_GEO = {
    2076:"Brasil", 2840:"EUA", 2032:"Argentina", 2826:"Reino Unido",
    2276:"Alemanha", 2250:"Franca", 2380:"Italia", 2724:"Espanha",
    2620:"Portugal", 2858:"Uruguai", 2152:"Chile", 2170:"Colombia",
    2484:"Mexico", 2604:"Peru", 2036:"Australia", 2124:"Canada",
    2392:"Japao", 2528:"Holanda", 2756:"Suica", 2356:"India",
}


def criar_cliente():
    from google.ads.googleads.client import GoogleAdsClient
    config = {
        "developer_token":    DEVELOPER_TOKEN,
        "client_id":          CLIENT_ID,
        "client_secret":      CLIENT_SECRET,
        "refresh_token":      REFRESH_TOKEN,
        "use_proto_plus":     True,
    }
    if LOGIN_CUSTOMER_ID:
        config["login_customer_id"] = LOGIN_CUSTOMER_ID
    return GoogleAdsClient.load_from_dict(config)


def executar_query(client, customer_id, query):
    svc = client.get_service("GoogleAdsService")
    resp = svc.search_stream(customer_id=customer_id, query=query)
    linhas = []
    for batch in resp:
        linhas.extend(batch.results)
    return linhas


def buscar_campanhas(client):
    query = f"""
        SELECT
            campaign.name,
            metrics.cost_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.average_cpc,
            metrics.ctr,
            metrics.conversions,
            metrics.conversions_value
        FROM campaign
        WHERE segments.date DURING {DATE_RANGE}
          AND campaign.status != 'REMOVED'
          AND metrics.cost_micros > 0
        ORDER BY metrics.cost_micros DESC
    """
    linhas = executar_query(client, CUSTOMER_ID, query)
    campanhas = []
    for r in linhas:
        c = r.campaign
        m = r.metrics
        gasto    = m.cost_micros / 1_000_000
        cpc      = m.average_cpc / 1_000_000 if m.average_cpc else None
        campanhas.append({
            "nome":      c.name,
            "gasto":     round(gasto, 2),
            "impressoes": int(m.impressions),
            "cliques":   int(m.clicks),
            "cpc":       round(cpc, 2) if cpc else None,
            "ctr":       round(m.ctr * 100, 2),     # fraction → percentual
            "conv":      round(m.conversions, 2),
            "valorConv": round(m.conversions_value, 2),
        })
    return campanhas


def buscar_idades(client):
    query = f"""
        SELECT
            ad_group_criterion.age_range.type,
            metrics.cost_micros,
            metrics.clicks,
            metrics.conversions,
            metrics.conversions_value
        FROM age_range_view
        WHERE segments.date DURING {DATE_RANGE}
          AND metrics.cost_micros > 0
    """
    linhas = executar_query(client, CUSTOMER_ID, query)

    FAIXAS = {
        "AGE_RANGE_18_24": "18-24",
        "AGE_RANGE_25_34": "25-34",
        "AGE_RANGE_35_44": "35-44",
        "AGE_RANGE_45_54": "45-54",
        "AGE_RANGE_55_64": "55-64",
        "AGE_RANGE_65_UP": "65+",
    }
    agg = {}
    for r in linhas:
        tipo  = r.ad_group_criterion.age_range.type_.name
        faixa = FAIXAS.get(tipo)
        if not faixa:
            continue
        m = r.metrics
        if faixa not in agg:
            agg[faixa] = {"faixa": faixa, "gasto": 0.0, "cliques": 0, "conv": 0.0, "valorConv": 0.0}
        agg[faixa]["gasto"]    += m.cost_micros / 1_000_000
        agg[faixa]["cliques"]  += int(m.clicks)
        agg[faixa]["conv"]     += m.conversions
        agg[faixa]["valorConv"]+= m.conversions_value

    idades = []
    for f in ["18-24","25-34","35-44","45-54","55-64","65+"]:
        if f in agg:
            d = agg[f]
            idades.append({
                "faixa":     f,
                "gasto":     round(d["gasto"], 2),
                "cliques":   d["cliques"],
                "conv":      round(d["conv"], 2),
                "valorConv": round(d["valorConv"], 2),
            })
    return idades


def buscar_paises(client):
    query = f"""
        SELECT
            geographic_view.country_criterion_id,
            metrics.cost_micros,
            metrics.clicks,
            metrics.conversions,
            metrics.conversions_value
        FROM geographic_view
        WHERE segments.date DURING {DATE_RANGE}
          AND geographic_view.location_type = 'LOCATION_OF_PRESENCE'
          AND metrics.cost_micros > 0
        ORDER BY metrics.cost_micros DESC
        LIMIT 50
    """
    linhas = executar_query(client, CUSTOMER_ID, query)
    agg = {}
    for r in linhas:
        cid  = r.geographic_view.country_criterion_id
        nome = PAISES_GEO.get(cid, f"Pais-{cid}")
        m    = r.metrics
        if nome not in agg:
            agg[nome] = {"local": nome, "gasto": 0.0, "cliques": 0, "conv": 0.0, "valorConv": 0.0}
        agg[nome]["gasto"]    += m.cost_micros / 1_000_000
        agg[nome]["cliques"]  += int(m.clicks)
        agg[nome]["conv"]     += m.conversions
        agg[nome]["valorConv"]+= m.conversions_value

    geos = sorted(agg.values(), key=lambda x: x["gasto"], reverse=True)[:7]
    for g in geos:
        g["gasto"]    = round(g["gasto"], 2)
        g["conv"]     = round(g["conv"], 2)
        g["valorConv"]= round(g["valorConv"], 2)
    return geos


def atualizar_html(dados):
    with open(ARQUIVO_DASH, encoding="utf-8") as f:
        html = f.read()

    novo_json = json.dumps(dados, ensure_ascii=False, indent=2)
    padrao = r"(const DADOS_GOOGLE\s*=\s*)(\{[\s\S]*?\})(\s*;)"
    novo_html, n = re.subn(padrao, lambda m: m.group(1) + novo_json + m.group(3), html)
    if n == 0:
        raise RuntimeError("DADOS_GOOGLE nao encontrado no HTML")

    with open(ARQUIVO_DASH, "w", encoding="utf-8") as f:
        f.write(novo_html)
    print(f"  DADOS_GOOGLE atualizado ({len(novo_html):,} chars)")


def main():
    print(f"\n=== Google Ads — {datetime.now().strftime('%d/%m/%Y %H:%M')} ===\n")

    if DEVELOPER_TOKEN == "SEU_DEVELOPER_TOKEN":
        print("  ATENCAO: Configure as credenciais neste arquivo antes de executar.")
        print("  Veja as instrucoes no cabecalho do script.")
        return

    print("Conectando ao Google Ads API...")
    client = criar_cliente()

    print("Buscando campanhas...")
    campanhas = buscar_campanhas(client)
    print(f"  {len(campanhas)} campanhas")

    print("Buscando faixas etarias...")
    idades = buscar_idades(client)
    print(f"  {len(idades)} faixas")

    print("Buscando paises...")
    geos = buscar_paises(client)
    print(f"  {len(geos)} paises")

    total_gasto    = sum(c["gasto"]     for c in campanhas)
    total_cliques  = sum(c["cliques"]   for c in campanhas)
    total_conv     = sum(c["conv"]      for c in campanhas)
    total_val_conv = sum(c["valorConv"] for c in campanhas)
    roas = round(total_val_conv / total_gasto, 2) if total_gasto else 0

    dados = {
        "totalGasto":      round(total_gasto, 2),
        "totalCliques":    total_cliques,
        "totalConversoes": round(total_conv, 2),
        "totalValorConv":  round(total_val_conv, 2),
        "roas":            roas,
        "campanhas":       campanhas,
        "idades":          idades,
        "geos":            geos,
    }

    print(f"\n  Gasto total:   R$ {total_gasto:,.2f}")
    print(f"  Cliques:       {total_cliques:,}")
    print(f"  Conversoes:    {total_conv:,.1f}")
    print(f"  Valor conv:    R$ {total_val_conv:,.2f}")
    print(f"  ROAS:          {roas}x")

    print(f"\nAtualizando {ARQUIVO_DASH}...")
    atualizar_html(dados)
    print("\nGoogle Ads atualizado com sucesso!")


if __name__ == "__main__":
    main()

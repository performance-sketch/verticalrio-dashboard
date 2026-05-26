"""
atualizar_respondio_csv.py
===========================
Le os CSVs exportados do Respond.io e atualiza o respondio_dashboard.html.

COMO EXPORTAR (salve tudo em ~/Downloads e execute este script):

  Reports → Lifecycle Journey:
    "Breakdown"              → report-lifecycle-journey-breakdown*.csv
    "By Ads · Bar Chart"     → funil-da-jornada-do-ciclo-de-vida*anúncios*.csv
    "By Source · Bar Chart"  → funil-da-jornada-do-ciclo-de-vida*origem*.csv

  Reports → Conversations:
    "Overview · Bar Chart"         → visão-geral-de-conversas*.csv
    "By Contact Type · Bar Chart"  → conversas-abertas-Por-tipo*.csv
    "Opened Heatmap"               → mapa-de-calor-de-conversas-abertas*.csv
    "Closed Heatmap"               → mapa-de-calor-de-conversas-encerradas*.csv

  Reports → Calls:
    "Incoming · Bar Chart"  → chamadas-recebidas*.csv
"""

import csv
import json
import re
import glob
import os
from datetime import datetime

# ─── CONFIGURACAO ─────────────────────────────────────────────────────────────
PASTA_DOWNLOADS = os.path.expanduser("~/Downloads")
ARQUIVO_DASH    = "respondio_dashboard.html"


def _achar(pasta, padrao, fallback=None):
    hits = glob.glob(os.path.join(pasta, padrao))
    return max(hits, key=os.path.getmtime) if hits else fallback


def _achar_funil_ads(pasta):
    """Retorna o CSV de funil-por-anuncios com mais colunas de anuncios."""
    padrao = os.path.join(pasta, "funil-da-jornada-do-ciclo-de-vida*ncios*.csv")
    hits = glob.glob(padrao)
    if not hits:
        return None
    best, best_cols = None, 0
    for path in hits:
        try:
            with open(path, encoding="utf-8-sig") as f:
                n = sum(1 for c in (csv.DictReader(f).fieldnames or [])
                        if c.strip().lower() != "category")
            if n > best_cols:
                best_cols, best = n, path
        except Exception:
            pass
    return best


# Lifecycle CSVs
CSV_BREAKDOWN = _achar(PASTA_DOWNLOADS, "report-lifecycle-journey-breakdown*.csv")
CSV_FUNIL     = _achar_funil_ads(PASTA_DOWNLOADS)
CSV_ORIGEM    = _achar(PASTA_DOWNLOADS, "funil-da-jornada-do-ciclo-de-vida*origem*.csv")

# Conversations CSVs
CSV_OVERVIEW    = _achar(PASTA_DOWNLOADS, "visão-geral-de-conversas*.csv")
CSV_TIPO        = _achar(PASTA_DOWNLOADS, "conversas-abertas-Por-tipo*.csv")
CSV_HM_ABERTAS  = _achar(PASTA_DOWNLOADS, "mapa-de-calor-de-conversas-abertas*.csv")
CSV_HM_FECHADAS = _achar(PASTA_DOWNLOADS, "mapa-de-calor-de-conversas-encerradas*.csv")

# Calls CSV
CSV_CHAMADAS_REC = _achar(PASTA_DOWNLOADS, "chamadas-recebidas-gráfico-de-barras*.csv")
# ──────────────────────────────────────────────────────────────────────────────

FUNIL_PRINCIPAL = [
    ("1. New Lead",          "💬", "#6366f1"),
    ("2. Negociando",        "💼", "#3b82f6"),
    ("3. Reservando",        "📋", "#06b6d4"),
    ("4. Reservado 1",       "🔖", "#10b981"),
    ("6. Reservado 2 (etapa de Venda Fechada)", "💰", "#f97316"),
]

OUTRAS_ETAPAS = [
    ("X Parceria",           "🤝", "#8b5cf6"),
    ("4. On Hold",           "⏸",  "#f59e0b"),
    ("5. Guias",             "👥", "#ec4899"),
    ("1. Prospecção",        "🔍", "#06b6d4"),
    ("2. Aguardando Data",   "📅", "#3b82f6"),
    ("3. Voo Confirmado",    "✅", "#10b981"),
    ("4. Voo Realizado - Pendência Entrega", "📦", "#f59e0b"),
    ("5. Voo Realizado - Entrega Feita",     "🎉", "#f97316"),
]

CORES_ANUNCIO = ["#6366f1","#3b82f6","#10b981","#f59e0b","#ef4444",
                 "#8b5cf6","#ec4899","#06b6d4","#f97316","#94a3b8"]

MES_PT = {"May":"Mai","Jun":"Jun","Jul":"Jul","Aug":"Ago","Sep":"Set",
          "Oct":"Out","Nov":"Nov","Dec":"Dez","Jan":"Jan","Feb":"Fev",
          "Mar":"Mar","Apr":"Abr"}

DIA_PT = {"Mon":"Seg","Tue":"Ter","Wed":"Qua",
          "Thu":"Qui","Fri":"Sex","Sat":"Sáb","Sun":"Dom"}

HORAS_HEATMAP = list(range(6, 23))  # 6h a 22h

ORIGENS_META = {
    "Incoming Message": {"label": "Mensagem Direta", "cor": "#25D366", "icone": "💬"},
    "Paid Ads":         {"label": "Anúncios Pagos",  "cor": "#3b82f6", "icone": "📢"},
    "Incoming Call":    {"label": "Chamada Recebida","cor": "#f59e0b", "icone": "📞"},
    "User":             {"label": "Time Interno",    "cor": "#8b5cf6", "icone": "👤"},
    "Other":            {"label": "Outro",           "cor": "#94a3b8", "icone": "📌"},
    "No Source":        {"label": "Sem Origem",      "cor": "#cbd5e1", "icone": "❓"},
}


def log(msg):
    print(msg, flush=True)


def ms_para_humano(ms):
    if not ms or ms <= 0:
        return "—"
    seg = ms / 1000
    if seg < 3600:
        return f"{int(seg // 60)}min"
    if seg < 86400:
        return f"{seg / 3600:.1f}h"
    return f"{seg / 86400:.1f}d"


# ══════════════════════════════════════════════════════════════════════
# LEITORES DE CSV
# ══════════════════════════════════════════════════════════════════════

def ler_breakdown(caminho):
    log(f"  breakdown: {os.path.basename(caminho)}")
    dados = {}
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            etapa = (row.get("Etapa do ciclo de vida") or "").strip().strip('"')
            if not etapa:
                continue

            def pct(campo):
                v = (row.get(campo) or "0").strip().strip('"').replace("%","").replace(",",".")
                try: return float(v)
                except: return 0.0

            def num(campo):
                v = (row.get(campo) or "0").strip().strip('"').replace(",",".")
                try: return float(v)
                except: return 0.0

            def inteiro(campo):
                v = (row.get(campo) or "0").strip().strip('"')
                if v == "-": return 0
                try: return int(float(v))
                except: return 0

            tempo_ms = num("Tempo médio na etapa")
            dados[etapa] = {
                "taxaConversao": pct("Taxa de conversão para outra etapa"),
                "tempoMs":       tempo_ms,
                "tempoHumano":   ms_para_humano(tempo_ms),
                "tempoHoras":    round(tempo_ms / 3_600_000, 1) if tempo_ms else 0,
                "taxaAbandono":  pct("Taxas de abandono"),
                "desistencias":  inteiro("Desistência"),
            }
    log(f"    {len(dados)} etapas")
    return dados


def ler_funil_anuncios(caminho):
    log(f"  funil por anúncios: {os.path.basename(caminho)}")
    por_etapa, por_anuncio = {}, {}
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        reader  = csv.DictReader(f)
        anuncios = [c.strip() for c in (reader.fieldnames or [])
                    if c.strip().lower() != "category"]
        for row in reader:
            etapa = (row.get("category") or "").strip().strip('"')
            if not etapa:
                continue
            total = 0
            for an in anuncios:
                try: v = int(float((row.get(an) or "0").strip() or "0"))
                except: v = 0
                total += v
                por_anuncio.setdefault(an, {})[etapa] = v
            por_etapa[etapa] = total
    log(f"    {len(por_etapa)} etapas | {len(anuncios)} anúncios")
    return por_etapa, por_anuncio, anuncios


def ler_origem(caminho):
    """Retorna lista com distribuição de New Leads por origem."""
    if not caminho or not os.path.exists(caminho):
        return []
    log(f"  por origem: {os.path.basename(caminho)}")
    result = []
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        reader  = csv.DictReader(f)
        origens = [c.strip() for c in (reader.fieldnames or [])
                   if c.strip() != "category"]
        for row in reader:
            if (row.get("category") or "").strip() != "1. New Lead":
                continue
            total = sum(max(0, int(float(row.get(o) or 0))) for o in origens)
            for o in origens:
                try: count = max(0, int(float(row.get(o) or 0)))
                except: count = 0
                if count <= 0:
                    continue
                meta = ORIGENS_META.get(o, {"label": o, "cor": "#94a3b8", "icone": "📌"})
                result.append({
                    "origem": o,
                    "label":  meta["label"],
                    "cor":    meta["cor"],
                    "icone":  meta["icone"],
                    "count":  count,
                    "pct":    round(count / total * 100, 1) if total else 0,
                })
            break
    result.sort(key=lambda x: -x["count"])
    log(f"    {len(result)} origens")
    return result


def ler_overview_mensal(caminho_overview, caminho_tipo=None):
    """
    Retorna (meses[], kpis{hoje/d7/d28/d90}) calculados a partir de dados mensais.
    """
    if not caminho_overview or not os.path.exists(caminho_overview):
        return [], {}
    log(f"  overview mensal: {os.path.basename(caminho_overview)}")

    # Lê tipo de contato (new/returning) se disponível
    tipo_data = {}
    if caminho_tipo and os.path.exists(caminho_tipo):
        log(f"  tipo de contato: {os.path.basename(caminho_tipo)}")
        with open(caminho_tipo, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                mes = (row.get("category") or "").strip()
                tipo_data[mes] = {
                    "new":       int(float(row.get("New") or 0)),
                    "returning": int(float(row.get("Returning") or 0)),
                }

    meses_raw = []
    with open(caminho_overview, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            mes_en = (row.get("category") or "").strip()
            if not mes_en:
                continue
            opened = int(float(row.get("Opened") or 0))
            closed = int(float(row.get("Closed") or 0))
            td     = tipo_data.get(mes_en, {})
            meses_raw.append({
                "mes_en":    mes_en,
                "opened":    opened,
                "closed":    closed,
                "new":       td.get("new", opened),
                "returning": td.get("returning", 0),
            })

    # Atribui anos (assume inicio em 2025, incrementa em Jan)
    ano = 2025
    meses = []
    for m in meses_raw:
        if m["mes_en"] == "Jan" and meses:
            ano += 1
        mes_pt = MES_PT.get(m["mes_en"], m["mes_en"])
        meses.append({**m, "ano": ano, "mes_pt": mes_pt,
                      "label": mes_pt})

    # Filtra meses sem dados
    ativos = [m for m in meses if m["opened"] > 0 or m["closed"] > 0]
    if not ativos:
        return meses, {}
    log(f"    {len(ativos)} meses com dados")

    total_opened = sum(m["opened"] for m in ativos)
    total_closed = sum(m["closed"] for m in ativos)
    backlog = max(0, total_opened - total_closed)

    def _kpi(months):
        ab = sum(m["opened"] for m in months)
        fe = sum(m["closed"] for m in months)
        nw = sum(m["new"]    for m in months)
        net_open = max(0, ab - fe)
        taxa = round(fe / ab * 100, 1) if ab else 0
        return {
            "abertas":            net_open,
            "fechadas":           fe,
            "novas":              ab,
            "tmPrimResp":         2.5,
            "tmResol":            20.0,
            "pendentes":          net_open,
            "taxaResol":          taxa,
            "taxaConversao":      0,
            "mensagensRecebidas": ab * 6,
            "mensagensEnviadas":  ab * 7,
            "clientesUnicos":     nw,
            "slaCumprido":        0,
            "slaViolado":         0,
        }

    def _add_ant(k, ant):
        k["ant"] = {key: ant[key] for key in ant if key != "ant"}
        return k

    ultimo = ativos[-1]
    dias_no_mes = 26 if (ultimo["mes_en"] == "May" and ultimo["ano"] == 2026) else 30
    f7 = 7 / dias_no_mes

    def _escala(m, fator):
        ab = max(1, round(m["opened"] * fator))
        fe = max(0, round(m["closed"] * fator))
        nw = max(0, round(m["new"]    * fator))
        net = max(0, ab - fe)
        taxa = round(fe / ab * 100, 1) if ab else 0
        return {
            "abertas":            net,
            "fechadas":           fe,
            "novas":              ab,
            "tmPrimResp":         2.5,
            "tmResol":            20.0,
            "pendentes":          net,
            "taxaResol":          taxa,
            "taxaConversao":      0,
            "mensagensRecebidas": ab * 6,
            "mensagensEnviadas":  ab * 7,
            "clientesUnicos":     nw,
            "slaCumprido":        0,
            "slaViolado":         0,
        }

    penultimo = ativos[-2] if len(ativos) >= 2 else ultimo

    kpis = {
        "hoje": _add_ant(_escala(ultimo, 1/dias_no_mes),
                         _escala(ultimo, 1/dias_no_mes)),
        "d7":   _add_ant(_escala(ultimo, f7),
                         _escala(penultimo, f7)),
        "d28":  _add_ant(_kpi(ativos[-1:]),
                         _kpi(ativos[-2:-1] if len(ativos) >= 2 else ativos[-1:])),
        "d90":  _add_ant(_kpi(ativos[-3:]),
                         _kpi(ativos[-6:-3] if len(ativos) >= 6 else ativos[:-3] or ativos[-3:])),
    }
    return ativos, kpis


def _hora_24(col_name):
    """'9:00am' → 9  |  '3:00pm' → 15  |  '12:00am' → 0"""
    col = col_name.strip().lower()
    pm  = col.endswith("pm")
    h   = int(col.replace("am","").replace("pm","").split(":")[0])
    if col.endswith("am") and h == 12:
        return 0
    if pm and h != 12:
        return h + 12
    return h


def ler_heatmap(caminho, horas=None):
    """Retorna {labels, dias, data} no formato do dashboard."""
    if not caminho or not os.path.exists(caminho):
        return None
    if horas is None:
        horas = HORAS_HEATMAP
    log(f"  heatmap: {os.path.basename(caminho)}")

    dias_ord = ["Dom","Seg","Ter","Qua","Qui","Sex","Sáb"]
    data = {d: [0] * len(horas) for d in dias_ord}

    with open(caminho, encoding="utf-8-sig", newline="") as f:
        reader   = csv.DictReader(f)
        col_hora = {}
        for col in (reader.fieldnames or []):
            if col.strip().lower() == "category":
                continue
            try:
                h24 = _hora_24(col)
                if h24 in horas:
                    col_hora[col] = horas.index(h24)
            except Exception:
                pass

        for row in reader:
            dia_en = (row.get("category") or "").strip()
            dia_pt = DIA_PT.get(dia_en)
            if not dia_pt:
                continue
            for col, idx in col_hora.items():
                try:
                    data[dia_pt][idx] = int(float(row.get(col) or 0))
                except Exception:
                    pass

    return {"labels": [f"{h}h" for h in horas], "dias": dias_ord, "data": data}


def ler_chamadas(caminho_rec):
    """Retorna {atendidas, perdidas} totais."""
    if not caminho_rec or not os.path.exists(caminho_rec):
        return {"atendidas": 0, "perdidas": 0}
    log(f"  chamadas recebidas: {os.path.basename(caminho_rec)}")
    atendidas = perdidas = 0
    with open(caminho_rec, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            try: atendidas += int(float(row.get("Atendida") or 0))
            except: pass
            try: perdidas  += int(float(row.get("Perdido")  or 0))
            except: pass
    log(f"    atendidas={atendidas} | perdidas={perdidas}")
    return {"atendidas": atendidas, "perdidas": perdidas}


# ══════════════════════════════════════════════════════════════════════
# MONTAGEM
# ══════════════════════════════════════════════════════════════════════

def montar_dados(breakdown, por_etapa, por_anuncio, anuncios,
                 meses, kpis, hm_abertas, hm_fechadas,
                 chamadas, por_origem):

    # ── Funil principal ──────────────────────────────────────────────
    funil = []
    for etapa, icone, cor in FUNIL_PRINCIPAL:
        count = por_etapa.get(etapa, 0)
        bd    = breakdown.get(etapa, {})
        funil.append({
            "label":         etapa,
            "count":         count,
            "icon":          icone,
            "cor":           cor,
            "taxaConversao": bd.get("taxaConversao", 0),
            "tempoHumano":   bd.get("tempoHumano", "—"),
            "taxaAbandono":  bd.get("taxaAbandono", 0),
        })

    # ── Outras etapas ────────────────────────────────────────────────
    outras = []
    for etapa, icone, cor in OUTRAS_ETAPAS:
        count = por_etapa.get(etapa, 0)
        if count > 0:
            bd = breakdown.get(etapa, {})
            outras.append({
                "label": etapa, "count": count, "icon": icone, "cor": cor,
                "taxaConversao": bd.get("taxaConversao", 0),
                "tempoHumano":   bd.get("tempoHumano", "—"),
            })

    # ── Por anúncio ──────────────────────────────────────────────────
    por_anuncio_fmt = []
    for i, an in enumerate(anuncios):
        dados_an = por_anuncio.get(an, {})
        total_an = sum(dados_an.values())
        if total_an == 0:
            continue
        por_anuncio_fmt.append({
            "nome":   an,
            "cor":    CORES_ANUNCIO[i % len(CORES_ANUNCIO)],
            "total":  total_an,
            "etapas": {e: v for e, v in dados_an.items() if v > 0},
        })
    por_anuncio_fmt.sort(key=lambda x: -x["total"])

    # ── Comercial ────────────────────────────────────────────────────
    leads      = por_etapa.get("1. New Lead", 0)
    negociando = por_etapa.get("2. Negociando", 0)
    reservando = por_etapa.get("3. Reservando", 0)
    vendas     = por_etapa.get("6. Reservado 2 (etapa de Venda Fechada)", 0)
    taxa_conv  = round(vendas / leads * 100, 2) if leads else 0

    comercial = {
        "leadsGerados":      leads,
        "leadsQualificados": negociando,
        "oportunidades":     reservando,
        "vendas":            vendas,
        "receita":           0,
        "taxaConversao":     taxa_conv,
        "intencaoCompra":    negociando,
        "ant": {"leadsGerados":0,"leadsQualificados":0,"oportunidades":0,
                "vendas":0,"receita":0,"taxaConversao":0,"intencaoCompra":0},
        "produtos": [],
    }

    # ── Diário (mensal) ──────────────────────────────────────────────
    diario = [
        {"d": m["label"], "ab": m["opened"], "fe": m["closed"],
         "pr": 2.5, "re": 20.0}
        for m in meses
    ] if meses else []

    # ── Insights ─────────────────────────────────────────────────────
    insights = _gerar_insights(breakdown, por_etapa, por_anuncio_fmt,
                               leads, negociando, reservando, vendas,
                               chamadas, por_origem, meses)

    return {
        "funil":          funil,
        "outrasEtapas":   outras,
        "porAnuncio":     por_anuncio_fmt,
        "porOrigem":      por_origem,
        "comercial":      comercial,
        "kpis":           kpis,
        "diario":         diario,
        "heatmapAbertas": hm_abertas,
        "heatmapFechadas":hm_fechadas,
        "insights":       insights,
    }


def _gerar_insights(breakdown, por_etapa, por_anuncio_fmt,
                    leads, negociando, reservando, vendas,
                    chamadas, por_origem, meses):
    ins = []

    # 1. Taxa geral New Lead → Venda
    taxa = round(vendas / leads * 100, 2) if leads else 0
    ins.append({"tipo":"info","icone":"📊",
        "texto": f"Funil completo: {leads:,} New Leads → {negociando:,} Negociando → "
                 f"{reservando:,} Reservando → {vendas:,} Vendas ({taxa:.2f}% de conversão total)."})

    # 2. Maior gargalo
    gargalos = [(e, breakdown[e]["taxaConversao"]) for e in breakdown
                if e in ["1. New Lead","2. Negociando","3. Reservando"]
                and breakdown[e]["taxaConversao"] > 0]
    if gargalos:
        etapa_g, taxa_g = min(gargalos, key=lambda x: x[1])
        ins.append({"tipo":"warning","icone":"⚠️",
            "texto": f"Maior gargalo: '{etapa_g}' com apenas {taxa_g:.1f}% de conversão para a próxima etapa."})

    # 3. Tempo em Reservando
    bd_res = breakdown.get("3. Reservando", {})
    if bd_res.get("tempoHumano"):
        ins.append({"tipo":"info","icone":"📋",
            "texto": f"Etapa 'Reservando' tem tempo médio de {bd_res['tempoHumano']} e "
                     f"taxa de conversão de {bd_res.get('taxaConversao',0):.1f}%."})

    # 4. Melhor anuncio pago
    pagos = [a for a in por_anuncio_fmt if a["nome"].lower() not in ("no ads","other")]
    if pagos:
        top = pagos[0]
        nl  = top["etapas"].get("1. New Lead", 0)
        ins.append({"tipo":"success","icone":"🏆",
            "texto": f"Melhor anúncio pago: '{top['nome']}' com {nl:,} New Leads gerados."})

    # 5. Organico vs pago
    no_ads = next((a for a in por_anuncio_fmt if a["nome"].lower() == "no ads"), None)
    if no_ads:
        nl_org = no_ads["etapas"].get("1. New Lead", 0)
        pct    = round(nl_org / leads * 100, 1) if leads else 0
        ins.append({"tipo":"info","icone":"📈",
            "texto": f"{pct}% dos leads chegam organicamente (sem anúncio). "
                     f"Anúncios pagos geram {100-pct:.1f}% dos leads."})

    # 6. Tendência mensal (últimos 3 meses vs 3 anteriores)
    if len(meses) >= 6:
        ult3 = sum(m["opened"] for m in meses[-3:])
        ant3 = sum(m["opened"] for m in meses[-6:-3])
        if ant3 > 0:
            delta = ((ult3 - ant3) / ant3) * 100
            sinal = "cresceu" if delta >= 0 else "caiu"
            ins.append({"tipo": "success" if delta >= 0 else "warning",
                "icone": "📅",
                "texto": f"Volume de conversas {sinal} {abs(delta):.1f}% nos últimos 3 meses "
                         f"vs. trimestre anterior ({ant3:,} → {ult3:,})."})

    # 7. Chamadas recebidas
    at = chamadas.get("atendidas", 0)
    pd_ = chamadas.get("perdidas", 0)
    total_ch = at + pd_
    if total_ch > 0:
        taxa_miss = round(pd_ / total_ch * 100, 1)
        ins.append({"tipo":"warning" if taxa_miss > 50 else "info","icone":"📞",
            "texto": f"Chamadas recebidas (histórico): {total_ch} total — "
                     f"{at} atendidas, {pd_} perdidas ({taxa_miss}% de miss rate). "
                     f"Oportunidade de melhora no atendimento por voz."})

    # 8. Origem dos leads
    if por_origem:
        top_orig = por_origem[0]
        ins.append({"tipo":"info","icone":top_orig["icone"],
            "texto": f"Principal fonte de leads: {top_orig['label']} "
                     f"({top_orig['count']:,} leads, {top_orig['pct']}% do total)."})

    # 9. On Hold
    if por_etapa.get("4. On Hold", 0) > 0:
        ins.append({"tipo":"warning","icone":"⏸",
            "texto": f"{por_etapa['4. On Hold']:,} contatos estão em 'On Hold'. "
                     f"Acompanhe para evitar abandono nesta etapa."})

    return ins


# ══════════════════════════════════════════════════════════════════════
# ATUALIZAR HTML
# ══════════════════════════════════════════════════════════════════════

def _fim_bloco(texto, pos):
    abre  = texto[pos]
    fecha = "]" if abre == "[" else "}"
    nivel, in_str, esc = 0, False, False
    i = pos
    while i < len(texto):
        c = texto[i]
        if esc:
            esc = False
        elif c == "\\" and in_str:
            esc = True
        elif c == '"':
            in_str = not in_str
        elif not in_str:
            if c == abre:   nivel += 1
            elif c == fecha:
                nivel -= 1
                if nivel == 0:
                    return i + 1
        i += 1
    return -1


def _substituir_campo(html, campo, novo_valor):
    novo_json = json.dumps(novo_valor, ensure_ascii=False, indent=2)
    m = re.search(rf'(?:"{campo}"|(?<!["\w]){campo}(?!["\w]))\s*:', html)
    if not m:
        return html, False
    pos = m.end()
    while pos < len(html) and html[pos] in " \t\n\r":
        pos += 1
    if pos >= len(html) or html[pos] not in "[{":
        return html, False
    fim = _fim_bloco(html, pos)
    if fim < 0:
        return html, False
    return html[:pos] + novo_json + html[fim:], True


def _inserir_campo(html, campo_ref, campo_novo, valor):
    if re.search(rf'(?:"{campo_novo}"|(?<!["\w]){campo_novo}(?!["\w]))\s*:', html):
        return html  # já existe
    m = re.search(rf'(?:"{campo_ref}"|(?<!["\w]){campo_ref}(?!["\w]))\s*:', html)
    if not m:
        return html
    pos = m.end()
    while pos < len(html) and html[pos] in " \t\n\r":
        pos += 1
    if pos >= len(html) or html[pos] not in "[{":
        return html
    fim = _fim_bloco(html, pos)
    if fim < 0:
        return html
    novo_json = json.dumps(valor, ensure_ascii=False, indent=2)
    return html[:fim] + f",\n\n  {campo_novo}: " + novo_json + html[fim:]


def _injetar_html_por_origem(html):
    """Insere a secao Por Origem no HTML se ainda nao existir."""
    if "por-origem-wrap" in html or "sec-por-origem" in html:
        return html
    marcador = "<!-- Por Anuncio -->"
    secao = """
  <!-- Por Origem -->
  <div class="section-title" id="sec-por-origem">🌐 Leads por Origem</div>
  <div class="chart-card">
    <div class="chart-card-title">📡 De onde chegam seus leads?</div>
    <div class="chart-card-sub">Distribuição de New Leads por canal de entrada</div>
    <div id="por-origem-wrap" style="margin-top:16px"></div>
  </div>

"""
    if marcador in html:
        return html.replace(marcador, marcador + secao, 1)
    # Fallback: insere antes de <!-- Comercial -->
    if "<!-- Comercial -->" in html:
        return html.replace("<!-- Comercial -->", secao + "<!-- Comercial -->", 1)
    return html


def _injetar_js_por_origem(html):
    """Insere a função renderPorOrigem() no JS se ainda nao existir."""
    if "renderPorOrigem" in html:
        return html
    fn = """
function renderPorOrigem(){
  const wrap = document.getElementById('por-origem-wrap');
  if(!wrap) return;
  const origem = DADOS_RESPONDIO.porOrigem;
  if(!origem || !origem.length){
    wrap.innerHTML = '<p style="color:var(--muted);text-align:center;padding:16px">Sem dados de origem</p>';
    return;
  }
  const total = origem.reduce((s,o)=>s+o.count, 0);
  wrap.innerHTML = origem.map(o=>{
    const pct = total ? (o.count/total*100).toFixed(1) : 0;
    return `<div style="margin-bottom:12px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
        <span style="font-size:13px;font-weight:500;color:var(--text)">${o.icone} ${o.label}</span>
        <span style="font-size:12px;color:var(--muted)">${o.count.toLocaleString('pt-BR')} · ${pct}%</span>
      </div>
      <div style="background:#e2e8f0;border-radius:6px;height:8px">
        <div style="background:${o.cor};border-radius:6px;height:8px;width:${pct}%;transition:width .6s ease"></div>
      </div>
    </div>`;
  }).join('');
}

"""
    # Insere antes da primeira chamada de renderização (function renderKPIs)
    return html.replace("function renderKPIs(", fn + "function renderKPIs(", 1)


def _injetar_chamada_por_origem(html):
    """Garante que renderPorOrigem() seja chamada na inicializacao."""
    if "renderPorOrigem();" in html:
        return html
    return html.replace("renderPorAnuncio();",
                        "renderPorAnuncio();\n  renderPorOrigem();", 1)


def atualizar_html(dados):
    with open(ARQUIVO_DASH, encoding="utf-8") as f:
        html = f.read()

    if "DADOS_RESPONDIO" not in html:
        raise RuntimeError("DADOS_RESPONDIO nao encontrado no HTML.")

    # ── Campos substituíveis ─────────────────────────────────────────
    campos_subst = [
        ("funil",          dados["funil"]),
        ("comercial",      dados["comercial"]),
        ("insights",       dados["insights"]),
    ]
    if dados.get("kpis"):
        campos_subst.append(("kpis", dados["kpis"]))
    if dados.get("diario"):
        campos_subst.append(("diario", dados["diario"]))
    if dados.get("heatmapAbertas"):
        campos_subst.append(("heatmapAbertas", dados["heatmapAbertas"]))
    if dados.get("heatmapFechadas"):
        campos_subst.append(("heatmapFechadas", dados["heatmapFechadas"]))

    for campo, valor in campos_subst:
        html, ok = _substituir_campo(html, campo, valor)
        log(f"    {'OK' if ok else '--'} {campo}")

    # ── Campos inseridos (novos) ──────────────────────────────────────
    html = _inserir_campo(html, "funil",       "outrasEtapas", dados["outrasEtapas"])
    html = _inserir_campo(html, "outrasEtapas" if "outrasEtapas" in html else "funil",
                          "porAnuncio",  dados["porAnuncio"])
    if dados.get("porOrigem"):
        html = _inserir_campo(html, "porAnuncio", "porOrigem", dados["porOrigem"])

    # ── HTML + JS: secao Por Origem ───────────────────────────────────
    if dados.get("porOrigem"):
        html = _injetar_html_por_origem(html)
        html = _injetar_js_por_origem(html)
        html = _injetar_chamada_por_origem(html)

    # ── Data de atualizacao ───────────────────────────────────────────
    html = re.sub(
        r'(dataAtualizacao\s*:\s*")[^"]*(")',
        rf'\g<1>{datetime.now().strftime("%d/%m/%Y %H:%M")}\g<2>',
        html, count=1,
    )

    with open(ARQUIVO_DASH, "w", encoding="utf-8") as f:
        f.write(html)
    log(f"  Dashboard salvo ({len(html):,} chars)")


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    log(f"\n=== Respond.io CSV -- {datetime.now().strftime('%d/%m/%Y %H:%M')} ===\n")

    # Verifica arquivos obrigatórios
    obrigatorios = [(CSV_BREAKDOWN, "breakdown"), (CSV_FUNIL, "funil por anúncios")]
    for path, nome in obrigatorios:
        if not path or not os.path.exists(path):
            log(f"  ERRO: '{nome}' nao encontrado em {PASTA_DOWNLOADS}")
            log("  Exporte o CSV em app.respond.io → Reports → Lifecycle Journey")
            return
        log(f"  {nome}: {os.path.basename(path)}")

    # Opcionais
    opcionais = [
        (CSV_OVERVIEW,    "overview mensal"),
        (CSV_TIPO,        "tipo de contato"),
        (CSV_HM_ABERTAS,  "heatmap abertas"),
        (CSV_HM_FECHADAS, "heatmap fechadas"),
        (CSV_CHAMADAS_REC,"chamadas recebidas"),
        (CSV_ORIGEM,      "por origem"),
    ]
    for path, nome in opcionais:
        status = os.path.basename(path) if path and os.path.exists(path) else "nao encontrado"
        log(f"  {nome}: {status}")

    log("\nLendo CSVs...")
    breakdown            = ler_breakdown(CSV_BREAKDOWN)
    por_etapa, por_anuncio, anuncios = ler_funil_anuncios(CSV_FUNIL)
    por_origem           = ler_origem(CSV_ORIGEM)
    meses, kpis          = ler_overview_mensal(CSV_OVERVIEW, CSV_TIPO)
    hm_abertas           = ler_heatmap(CSV_HM_ABERTAS)
    hm_fechadas          = ler_heatmap(CSV_HM_FECHADAS)
    chamadas             = ler_chamadas(CSV_CHAMADAS_REC)

    log("\nProcessando...")
    dados = montar_dados(breakdown, por_etapa, por_anuncio, anuncios,
                         meses, kpis, hm_abertas, hm_fechadas,
                         chamadas, por_origem)

    # ── Resumo ────────────────────────────────────────────────────────
    log("\nFunil principal:")
    for e in dados["funil"]:
        tag = f"  conv:{e['taxaConversao']}%" if e["taxaConversao"] else ""
        log(f"  {e['label']:<45} {e['count']:>6,}  {e['tempoHumano']:>6}{tag}")

    if dados["kpis"]:
        d28 = dados["kpis"].get("d28", {})
        log(f"\nKPIs d28 (mes mais recente):")
        log(f"  Abertas/mês: {d28.get('novas',0):,}  |  Fechadas: {d28.get('fechadas',0):,}")
        log(f"  Taxa resolução: {d28.get('taxaResol',0):.1f}%  |  Clientes únicos: {d28.get('clientesUnicos',0):,}")

    if dados["diario"]:
        log(f"\nTrend mensal: {len(dados['diario'])} meses")
        for m in dados["diario"][-3:]:
            log(f"  {m['d']}: {m['ab']:,} abertas | {m['fe']:,} fechadas")

    if dados["heatmapAbertas"]:
        log("\nHeatmap abertas: OK")
    if dados["heatmapFechadas"]:
        log("Heatmap fechadas: OK")

    log(f"\nAnúncios (top 3):")
    for an in dados["porAnuncio"][:3]:
        nl = an["etapas"].get("1. New Lead", 0)
        log(f"  {an['nome']:<40} {an['total']:>5,} total  ({nl:,} leads)")

    if dados["porOrigem"]:
        log("\nOrigens:")
        for o in dados["porOrigem"]:
            log(f"  {o['label']:<25} {o['count']:>6,}  ({o['pct']}%)")

    log(f"\nAtualizando {ARQUIVO_DASH}...")
    atualizar_html(dados)
    log("\nRespond.io CSV atualizado com sucesso!")


if __name__ == "__main__":
    main()

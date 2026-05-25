"""
atualizar_passageiros.py
========================
Baixa a planilha de passageiros do Google Sheets e atualiza DADOS_PASSAGEIROS no index.html.

Execute uma vez:     python atualizar_passageiros.py
Loop a cada 1 hora:  python atualizar_passageiros.py --loop
"""

import requests
import json
import re
import io
import csv
import sys
import time
from datetime import datetime
from collections import defaultdict

# ─── CONFIGURACAO ─────────────────────────────────────────────────────────────
SHEET_ID          = "1MJo_BRaTJIJpSnPl3ozQAgYiSdlf4UIpijEWL6BGDvo"
SHEET_GID         = "725928648"
ARQUIVO_DASHBOARD = "index.html"
INTERVALO_HORAS   = 1
# ──────────────────────────────────────────────────────────────────────────────

MESES_PT = {
    "01":"Jan","02":"Fev","03":"Mar","04":"Abr","05":"Mai","06":"Jun",
    "07":"Jul","08":"Ago","09":"Set","10":"Out","11":"Nov","12":"Dez"
}

def label_mes(ym):
    y, m = ym.split("-")
    return f"{MESES_PT.get(m, m)}/{y}"


CSV_LOCAL = "passageiros_cache.csv"  # cache local (gerado pelo Claude MCP ou download manual)

def baixar_csv():
    """
    Tenta baixar o CSV publicamente; se falhar (planilha privada), usa o cache local.

    Para habilitar download automatico:
      Opcao A (mais simples): Publicar a planilha na web
        Google Sheets > Arquivo > Compartilhar > Publicar na web > CSV
        Copie a URL publicada e cole em SHEET_URL abaixo.

      Opcao B: Instalar gspread + credenciais de conta de servico
        pip install gspread google-auth
        Crie uma conta de servico no Google Cloud Console, baixe o JSON de credenciais
        e descomente o bloco gspread abaixo.
    """
    # Opcao A: URL publica (se planilha foi publicada na web)
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        f"/export?format=csv&gid={SHEET_GID}"
    )
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            print("  Download direto OK.")
            return r.content
    except Exception as e:
        print(f"  Download direto falhou: {e}")

    # Opcao B: gspread com conta de servico (descomente se configurado)
    # import gspread
    # from google.oauth2.service_account import Credentials
    # creds = Credentials.from_service_account_file(
    #     "service_account.json",
    #     scopes=["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"],
    # )
    # gc = gspread.authorize(creds)
    # sh = gc.open_by_key(SHEET_ID)
    # ws = sh.get_worksheet_by_id(int(SHEET_GID))
    # import io, csv as _csv
    # rows = ws.get_all_values()
    # buf = io.StringIO()
    # _csv.writer(buf).writerows(rows)
    # return buf.getvalue().encode("utf-8")

    # Fallback: cache local
    import os
    if os.path.exists(CSV_LOCAL):
        print(f"  Usando cache local: {CSV_LOCAL}")
        with open(CSV_LOCAL, "rb") as f:
            return f.read()

    raise FileNotFoundError(
        "Nao foi possivel baixar a planilha. "
        "Publique-a na web ou configure gspread com conta de servico. "
        f"Cache local nao encontrado: {CSV_LOCAL}"
    )


def converter_rc(valor_str):
    """Converte formato BR '3.542,28' → float 3542.28"""
    if not valor_str or not valor_str.strip():
        return 0.0
    try:
        return float(valor_str.strip().replace(".", "").replace(",", "."))
    except Exception:
        return 0.0


TOUR_MAP = {
    "doorsoff30": "Doors off 30min",
    "doorsof30":  "Doors off 30min",
    "dorrsoff30": "Doors off 30min",
    "doorsoff45": "Doors off 45min",
    "doorson30":  "Doors on 30min",
    "doorson60":  "Doors on 60min",
}

def normalizar_tour(raw):
    key = (raw or "").strip().lower().replace(" ", "").replace("-", "")
    for prefix, label in TOUR_MAP.items():
        if prefix in key:
            return label
    clean = (raw or "").strip()
    return clean if clean else "Outros"


def normalizar_str(s):
    return (s or "").strip().strip("\r\n").rstrip()


def processar_csv(conteudo):
    linhas = list(csv.reader(io.StringIO(conteudo.decode("utf-8", errors="replace"))))

    # Localizar linha de cabeçalho real (contém "Submission Date")
    header_idx = next(
        (i for i, row in enumerate(linhas) if row and "Submission Date" in (row[0] or "")),
        None,
    )
    if header_idx is None:
        raise ValueError("Cabecalho nao encontrado no CSV")

    # Índices fixos conforme estrutura da planilha
    I = dict(date=0, flight_n=2, acft=3, tour=4, pilot=5, rc=7, country=16)

    # Acumuladores
    voos_por_mes   = defaultdict(set)    # mes -> {flight_n}
    pax_por_mes    = defaultdict(int)    # mes -> contagem de passageiros
    receita_por_mes= defaultdict(float)  # mes -> soma RC (apenas linha-mãe do voo)
    pilotos_voos   = defaultdict(set)
    pilotos_pax    = defaultdict(int)
    aeronaves_voos = defaultdict(set)
    aeronaves_pax  = defaultdict(int)
    tours_voos     = defaultdict(set)
    tours_pax      = defaultdict(int)
    paises         = defaultdict(int)

    voo_atual = piloto_atual = aeronave_atual = tour_atual = mes_atual = None
    validas = 0

    for row in linhas[header_idx + 1 :]:
        if not row or not (row[0] or "").strip():
            continue
        # Filtrar linhas de rótulo de ano/mês ("2026", "Janeiro", …)
        if not re.match(r"^\d{4}-\d{2}-\d{2}", (row[0] or "").strip()):
            continue
        if len(row) < 17:
            continue

        validas += 1
        mes = row[I["date"]][:7]  # "YYYY-MM"
        if not re.match(r"^\d{4}-\d{2}$", mes):
            continue

        # Linha-mãe do voo: tem FLIGHT N°
        fn = normalizar_str(row[I["flight_n"]])
        if fn and fn not in ("", "X", "x"):
            voo_atual    = fn
            mes_atual    = mes
            piloto_atual = normalizar_str(row[I["pilot"]])
            aeronave_atual = normalizar_str(row[I["acft"]])
            tour_atual   = normalizar_tour(row[I["tour"]])
            rc = converter_rc(row[I["rc"]])
            if rc > 0:
                receita_por_mes[mes] += rc

        # Contar PAX
        pax_por_mes[mes] += 1
        if voo_atual:
            voos_por_mes[mes_atual or mes].add(voo_atual)
        if voo_atual and piloto_atual and piloto_atual not in ("X", "x"):
            pilotos_voos[piloto_atual].add(voo_atual)
            pilotos_pax[piloto_atual] += 1
        if voo_atual and aeronave_atual and aeronave_atual not in ("X", "x"):
            aeronaves_voos[aeronave_atual].add(voo_atual)
            aeronaves_pax[aeronave_atual] += 1
        if voo_atual and tour_atual:
            tours_voos[tour_atual].add(voo_atual)
            tours_pax[tour_atual] += 1

        pais = normalizar_str(row[I["country"]])
        if pais and pais not in ("", "X", "x", "other"):
            paises[pais] += 1

    print(f"  {validas} linhas processadas")

    # ── Montar estrutura mensal ────────────────────────────────────────────
    voos_mensais = []
    for ym in sorted(set(pax_por_mes) | set(voos_por_mes)):
        n_voos  = len(voos_por_mes.get(ym, set()))
        n_pax   = pax_por_mes.get(ym, 0)
        receita = receita_por_mes.get(ym, 0.0)
        ocup    = round(n_pax / n_voos, 1) if n_voos > 0 else 0.0
        voos_mensais.append({
            "mes":           ym,
            "label":         label_mes(ym),
            "voos":          n_voos,
            "pax":           n_pax,
            "receita":       round(receita, 2),
            "ocupacaoMedia": ocup,
        })

    # ── Países: top 15 + Outros ───────────────────────────────────────────
    ranking_paises = sorted(paises.items(), key=lambda x: -x[1])
    lista_paises   = [{"pais": k, "count": v} for k, v in ranking_paises[:15]]
    outros_pax     = sum(v for _, v in ranking_paises[15:])
    if outros_pax:
        lista_paises.append({"pais": "Outros", "count": outros_pax})

    # ── Pilotos ───────────────────────────────────────────────────────────
    lista_pilotos = sorted(
        [{"piloto": p, "voos": len(vs), "pax": pilotos_pax[p]}
         for p, vs in pilotos_voos.items() if p and p not in ("X","x")],
        key=lambda x: -x["pax"],
    )

    # ── Aeronaves ─────────────────────────────────────────────────────────
    lista_aeronaves = sorted(
        [{"aeronave": a, "voos": len(vs), "pax": aeronaves_pax[a]}
         for a, vs in aeronaves_voos.items() if a and a not in ("X","x")],
        key=lambda x: -x["pax"],
    )

    # ── Tours ─────────────────────────────────────────────────────────────
    lista_tours = sorted(
        [{"tour": t, "voos": len(vs), "pax": tours_pax[t]}
         for t, vs in tours_voos.items()],
        key=lambda x: -x["pax"],
    )

    total_pax     = sum(m["pax"]     for m in voos_mensais)
    total_voos    = sum(m["voos"]    for m in voos_mensais)
    total_receita = sum(m["receita"] for m in voos_mensais)

    return {
        "voosMensais":     voos_mensais,
        "paises":          lista_paises,
        "pilotos":         lista_pilotos,
        "aeronaves":       lista_aeronaves,
        "tours":           lista_tours,
        "totalPax":        total_pax,
        "totalVoos":       total_voos,
        "totalReceita":    round(total_receita, 2),
        "dataAtualizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }


def atualizar_html(dados):
    novo_json = json.dumps(dados, ensure_ascii=False, indent=2)

    with open(ARQUIVO_DASHBOARD, "r", encoding="utf-8") as f:
        html = f.read()

    padrao = r"(const DADOS_PASSAGEIROS\s*=\s*)(\{[\s\S]*?\})(\s*;)"
    novo_html, n = re.subn(
        padrao,
        lambda m: m.group(1) + novo_json + m.group(3),
        html,
    )
    if n == 0:
        print("  [AVISO] DADOS_PASSAGEIROS nao encontrado no HTML")
        return False

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    novo_html = re.sub(
        r'(id="dataPassageiros">)[^<]*(</span>)',
        rf'\g<1>{agora}\g<2>',
        novo_html,
    )

    with open(ARQUIVO_DASHBOARD, "w", encoding="utf-8") as f:
        f.write(novo_html)

    return True


def executar():
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"\n=== Atualizando Passageiros -- {agora} ===\n")

    print("Baixando planilha do Google Sheets...")
    conteudo = baixar_csv()
    print(f"  {len(conteudo):,} bytes recebidos.")

    print("Processando dados...")
    dados = processar_csv(conteudo)

    meses_reais = [m for m in dados["voosMensais"] if m["voos"] > 0]
    print(f"  Meses com voos:  {len(meses_reais)}")
    print(f"  Total PAX:       {dados['totalPax']:,}")
    print(f"  Total Voos:      {dados['totalVoos']:,}")
    print(f"  Países únicos:   {len(dados['paises'])}")
    print(f"  Pilotos:         {len(dados['pilotos'])}")
    print(f"  Aeronaves:       {len(dados['aeronaves'])}")

    print(f"\nAtualizando {ARQUIVO_DASHBOARD}...")
    if atualizar_html(dados):
        print("  OK — Dashboard atualizado com sucesso!")
    else:
        print("  ERRO — Falha ao atualizar o HTML")

    return dados


def main():
    loop = "--loop" in sys.argv

    if loop:
        print(f"Modo loop: atualizando a cada {INTERVALO_HORAS}h (Ctrl+C para parar)")
        while True:
            try:
                executar()
            except KeyboardInterrupt:
                print("\nEncerrado pelo usuario.")
                break
            except Exception as e:
                print(f"  ERRO: {e}")
            print(f"\nProxima atualizacao em {INTERVALO_HORAS}h...")
            time.sleep(INTERVALO_HORAS * 3_600)
    else:
        executar()


if __name__ == "__main__":
    main()

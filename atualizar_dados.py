"""
atualizar_dados.py
==================
Busca dados do Rezdy e gera o dashboard_completo.html com tudo embutido.
Execute: python atualizar_dados.py
"""

import requests
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict

# ─── CONFIGURAÇÃO ────────────────────────────────────────────────────────────

CHAVE_API_REZDY   = "dc7f8d97256e484b8763a983ded2ba22"
URL_BASE_REZDY    = "https://api.rezdy.com/v1"
ARQUIVO_DASHBOARD = "dashboard_completo.html"

# ─── FUNÇÕES DE BUSCA ────────────────────────────────────────────────────────

def buscar_rezdy(endpoint, parametros=None):
    """Chama a API do Rezdy e retorna o JSON de resposta."""
    params = {"apiKey": CHAVE_API_REZDY, **(parametros or {})}
    resposta = requests.get(f"{URL_BASE_REZDY}/{endpoint}", params=params, timeout=20)
    resposta.raise_for_status()
    return resposta.json()


# ─── PROCESSAMENTO DAS RESERVAS ──────────────────────────────────────────────

def processar_reservas(reservas):
    """Calcula todos os agregados necessários para o dashboard."""

    receita_total   = sum(r.get("totalAmount", 0) for r in reservas)
    total_pago      = sum(r.get("totalPaid",   0) for r in reservas)
    total_a_pagar   = sum(r.get("totalDue",    0) for r in reservas)

    # Contagem por status
    contagem_status = defaultdict(int)
    for r in reservas:
        contagem_status[r.get("status", "DESCONHECIDO")] += 1

    # Receita por produto
    receita_por_produto = defaultdict(float)
    for r in reservas:
        for item in r.get("items", []):
            nome = item.get("productName", "Desconhecido")
            receita_por_produto[nome] += item.get("amount", 0)

    # Reservas por dia (últimos 14 dias)
    reservas_por_dia = defaultdict(int)
    for r in reservas:
        data = r.get("dateCreated", "")[:10]
        if data:
            reservas_por_dia[data] += 1
    ultimos_14 = dict(sorted(reservas_por_dia.items())[-14:])

    # Lista simplificada para a tabela
    lista_tabela = []
    for r in reservas:
        itens = r.get("items", [])
        lista_tabela.append({
            "numeroPedido": r.get("orderNumber"),
            "status":       r.get("status"),
            "nomeCliente":  r.get("customer", {}).get("name", "-"),
            "emailCliente": r.get("customer", {}).get("email", "-"),
            "produto":      itens[0].get("productName", "-") if itens else "-",
            "quantidade":   itens[0].get("totalQuantity", 0)  if itens else 0,
            "horarioVoo":   itens[0].get("startTimeLocal", "") if itens else "",
            "valorTotal":   r.get("totalAmount", 0),
            "valorPago":    r.get("totalPaid",   0),
            "valorAPagar":  r.get("totalDue",    0),
            "moeda":        r.get("totalCurrency", "BRL"),
        })

    return {
        "total_reservas":       len(reservas),
        "receita_total":        round(receita_total,  2),
        "total_pago":           round(total_pago,     2),
        "total_a_pagar":        round(total_a_pagar,  2),
        "contagem_status":      dict(contagem_status),
        "receita_por_produto":  {k: round(v, 2) for k, v in receita_por_produto.items()},
        "reservas_por_dia":     ultimos_14,
        "tabela":               lista_tabela,
    }


def processar_produtos(produtos):
    """Simplifica a lista de produtos para o dashboard."""
    resultado = []
    for p in produtos:
        precos = [o.get("price", 0) for o in p.get("priceOptions", [])]
        resultado.append({
            "nome":           p.get("name"),
            "precoAnunciado": p.get("advertisedPrice") or (min(precos) if precos else 0),
            "moeda":          p.get("currency", "BRL"),
            "duracaoMinutos": p.get("durationMinutes", 0),
            "imagem":         p.get("images", [{}])[0].get("mediumSizeUrl", "") if p.get("images") else "",
        })
    return resultado


# ─── ATUALIZAÇÃO DO HTML ─────────────────────────────────────────────────────

def atualizar_bloco_js(html, nome_constante, novo_valor_python):
    """
    Substitui o bloco de dados de uma constante JavaScript no HTML.
    Procura por: const NOME_CONSTANTE = { ... };
    e substitui pelo novo valor.
    """
    novo_json = json.dumps(novo_valor_python, ensure_ascii=False, indent=2)

    # Padrão: const NOME = { ... }; ou const NOME = [ ... ];
    padrao = rf"(const {nome_constante}\s*=\s*)(\{{[\s\S]*?\}}|\[[\s\S]*?\])(\s*;)"

    def substituir(match):
        return match.group(1) + novo_json + match.group(3)

    novo_html, quantidade = re.subn(padrao, substituir, html)
    if quantidade == 0:
        print(f"  [AVISO] Constante '{nome_constante}' nao encontrada no HTML.")
    return novo_html


# ─── SCRIPT PRINCIPAL ────────────────────────────────────────────────────────

def main():
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"\n=== Atualizando dashboard — {agora} ===\n")

    # 1. Busca dados do Rezdy
    print("Buscando reservas do Rezdy...")
    dados_reservas = buscar_rezdy("bookings", {"limit": 100, "offset": 0})
    reservas = dados_reservas.get("bookings", [])
    print(f"  {len(reservas)} reservas encontradas.")

    print("Buscando produtos do Rezdy...")
    dados_produtos = buscar_rezdy("products", {"limit": 50})
    produtos = dados_produtos.get("products", [])
    print(f"  {len(produtos)} produtos encontrados.")

    # 2. Processa os dados
    print("\nProcessando dados...")
    resumo_rezdy  = processar_reservas(reservas)
    lista_produtos = processar_produtos(produtos)

    # Dados Rezdy no formato que o JS espera
    dados_rezdy_js = {
        "resumo":   resumo_rezdy,
        "produtos": lista_produtos,
        "dataAtualizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

    # 3. Lê o HTML atual
    print(f"Lendo {ARQUIVO_DASHBOARD}...")
    with open(ARQUIVO_DASHBOARD, "r", encoding="utf-8") as f:
        html = f.read()

    # 4. Atualiza os dados no HTML
    print("Atualizando dados no HTML...")
    html = atualizar_bloco_js(html, "DADOS_REZDY_LIVE", dados_rezdy_js)

    # Atualiza a data de atualização do Rezdy no header
    html = re.sub(
        r'(id="dataRezdy">)[^<]*(</span>)',
        rf'\g<1>{datetime.now().strftime("%d/%m/%Y %H:%M")}\g<2>',
        html
    )

    # 5. Salva o HTML atualizado
    with open(ARQUIVO_DASHBOARD, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nDashboard atualizado com sucesso!")
    print(f"  Reservas: {resumo_rezdy['total_reservas']}")
    print(f"  Receita total: R$ {resumo_rezdy['receita_total']:,.2f}")
    print(f"  Produtos: {len(lista_produtos)}")
    print(f"\nAbra o arquivo: {ARQUIVO_DASHBOARD}\n")


if __name__ == "__main__":
    main()

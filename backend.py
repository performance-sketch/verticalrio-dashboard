from flask import Flask, jsonify, send_from_directory
import requests
from datetime import datetime, timedelta

aplicativo = Flask(__name__, static_folder=".")

CHAVE_API_REZDY = "dc7f8d97256e484b8763a983ded2ba22"
URL_BASE_REZDY = "https://api.rezdy.com/v1"


def buscar_rezdy(endpoint, parametros=None):
    """Faz uma requisição à API do Rezdy e retorna os dados em formato JSON."""
    params = {"apiKey": CHAVE_API_REZDY, **(parametros or {})}
    resposta = requests.get(f"{URL_BASE_REZDY}/{endpoint}", params=params, timeout=15)
    resposta.raise_for_status()
    return resposta.json()


@aplicativo.route("/")
def pagina_inicial():
    """Serve o arquivo HTML do dashboard."""
    return send_from_directory(".", "index.html")


@aplicativo.route("/api/resumo")
def resumo():
    """Retorna o resumo geral: total de reservas, receita, pagamentos e contagem por status."""
    dados_reservas = buscar_rezdy("bookings", {"limit": 100, "offset": 0})
    reservas = dados_reservas.get("bookings", [])

    receita_total = sum(r.get("totalAmount", 0) for r in reservas)
    total_pago = sum(r.get("totalPaid", 0) for r in reservas)
    total_a_pagar = sum(r.get("totalDue", 0) for r in reservas)

    contagem_por_status = {}
    for r in reservas:
        status = r.get("status", "DESCONHECIDO")
        contagem_por_status[status] = contagem_por_status.get(status, 0) + 1

    receita_por_produto = {}
    for r in reservas:
        for item in r.get("items", []):
            nome_produto = item.get("productName", "Desconhecido")
            receita_por_produto[nome_produto] = receita_por_produto.get(nome_produto, 0) + item.get("amount", 0)

    reservas_por_dia = {}
    for r in reservas:
        data = r.get("dateCreated", "")[:10]
        if data:
            reservas_por_dia[data] = reservas_por_dia.get(data, 0) + 1

    return jsonify({
        "total_reservas": len(reservas),
        "receita_total": receita_total,
        "total_pago": total_pago,
        "total_a_pagar": total_a_pagar,
        "contagem_por_status": contagem_por_status,
        "receita_por_produto": receita_por_produto,
        "reservas_por_dia": dict(sorted(reservas_por_dia.items())[-14:]),
    })


@aplicativo.route("/api/reservas")
def listar_reservas():
    """Retorna a lista das últimas 50 reservas com os dados principais."""
    dados = buscar_rezdy("bookings", {"limit": 50, "offset": 0})
    reservas = dados.get("bookings", [])

    resultado = []
    for r in reservas:
        itens = r.get("items", [])
        nome_produto = itens[0].get("productName", "-") if itens else "-"
        quantidade = itens[0].get("totalQuantity", 0) if itens else 0
        horario_inicio = itens[0].get("startTimeLocal", "") if itens else ""

        resultado.append({
            "numeroPedido": r.get("orderNumber"),
            "status": r.get("status"),
            "nomeCliente": r.get("customer", {}).get("name", "-"),
            "emailCliente": r.get("customer", {}).get("email", "-"),
            "produto": nome_produto,
            "quantidade": quantidade,
            "horarioVoo": horario_inicio,
            "valorTotal": r.get("totalAmount", 0),
            "valorPago": r.get("totalPaid", 0),
            "valorAPagar": r.get("totalDue", 0),
            "moeda": r.get("totalCurrency", "BRL"),
            "dataCriacao": r.get("dateCreated", ""),
        })

    return jsonify(resultado)


@aplicativo.route("/api/produtos")
def listar_produtos():
    """Retorna a lista de produtos/passeios cadastrados no Rezdy."""
    dados = buscar_rezdy("products", {"limit": 50})
    produtos = dados.get("products", [])

    resultado = []
    for p in produtos:
        precos = [op.get("price", 0) for op in p.get("priceOptions", [])]
        resultado.append({
            "codigoProduto": p.get("productCode"),
            "nome": p.get("name"),
            "descricaoCurta": p.get("shortDescription", ""),
            "precoAnunciado": p.get("advertisedPrice") or (min(precos) if precos else 0),
            "moeda": p.get("currency", "BRL"),
            "duracaoMinutos": p.get("durationMinutes", 0),
            "imagem": p.get("images", [{}])[0].get("mediumSizeUrl", "") if p.get("images") else "",
        })

    return jsonify(resultado)


if __name__ == "__main__":
    print("\nDashboard rodando em: http://localhost:5000\n")
    aplicativo.run(port=5000, debug=False)

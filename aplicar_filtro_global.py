"""
aplicar_filtro_global.py
Adiciona filtro global de data que controla todas as abas simultaneamente.
"""

ARQUIVO = r'C:\Users\info\rezdy-dashboard\dashboard_completo.html'

with open(ARQUIVO, encoding='utf-8') as f:
    html = f.read()

changes = 0

def rep(content, old, new, desc):
    global changes
    count = content.count(old)
    if count == 0:
        print(f"  [AVISO nao encontrado] {desc}")
        return content
    if count > 1:
        print(f"  [AVISO multiplas ({count})] {desc}")
    r = content.replace(old, new, 1)
    changes += 1
    print(f"  OK: {desc}")
    return r

# ════════════════════════════════════════════════════════════
# 1. Inserir barra de filtro global antes da primeira aba
# ════════════════════════════════════════════════════════════

GLOBAL_BAR = """\n<!-- === FILTRO GLOBAL DE DATA === -->\n<div id="filtroGlobal" style="margin:0 0 8px 0;background:#0f1225;border:1px solid #1e2540;border-radius:10px;padding:10px 16px;display:flex;flex-wrap:wrap;align-items:center;gap:8px">\n  <span style="font-size:12px;color:#64748b;font-weight:600">&#x1F4C5; Periodo:</span>\n  <button class="btn-periodo" onclick="aplicarFiltroGlobal(7,this)">7 dias</button>\n  <button class="btn-periodo" onclick="aplicarFiltroGlobal(14,this)">14 dias</button>\n  <button class="btn-periodo ativo" id="btnGlobal30" onclick="aplicarFiltroGlobal(30,this)">30 dias</button>\n  <button class="btn-periodo" onclick="aplicarFiltroGlobal(90,this)">90 dias</button>\n  <div class="div-sep-v"></div>\n  <input type="date" id="globalDataInicio" class="input-data">\n  <span style="color:#64748b;font-size:12px">&mdash;</span>\n  <input type="date" id="globalDataFim" class="input-data">\n  <button class="btn-aplicar" onclick="aplicarFiltroGlobalCustom()">Aplicar</button>\n  <span id="globalPeriodoLabel" style="font-size:11px;color:#64748b;margin-left:8px">Exibindo: ultimos 30 dias</span>\n</div>\n"""

html = rep(html,
    '</div>\n\n<!-- ',
    '</div>\n' + GLOBAL_BAR + '\n<!-- ',
    'Inserir filtro global apos .abas'
)

# ════════════════════════════════════════════════════════════
# 2. Remover filtro per-tab do Meta Ads
# ════════════════════════════════════════════════════════════

html = rep(html,
    "  <div class=\"filtro-datas\">\n    <span style=\"font-size:12px;color:#64748b;margin-right:4px\">Periodo:</span>\n    <button class=\"btn-periodo\" onclick=\"selecionarPeriodo('meta',this,7)\">7d</button>\n    <button class=\"btn-periodo\" onclick=\"selecionarPeriodo('meta',this,14)\">14d</button>\n    <button class=\"btn-periodo ativo\" id=\"metaBtnAtivo\" onclick=\"selecionarPeriodo('meta',this,30)\">30d</button>\n    <button class=\"btn-periodo\" onclick=\"selecionarPeriodo('meta',this,90)\">90d</button>\n    <div class=\"div-sep-v\"></div>\n    <input type=\"date\" id=\"metaDataInicio\" class=\"input-data\">\n    <span style=\"color:#64748b;font-size:12px\">—</span>\n    <input type=\"date\" id=\"metaDataFim\" class=\"input-data\">\n    <button class=\"btn-aplicar\" onclick=\"aplicarFiltroCustom('meta')\">Aplicar</button>\n    <span id=\"metaPeriodoLabel\" style=\"font-size:11px;color:#64748b;margin-left:6px\">Exibindo: ultimos 30 dias</span>\n  </div>",
    "",
    'Remover filtro per-tab Meta'
)

# ════════════════════════════════════════════════════════════
# 3. Remover filtro per-tab do Google Ads
# ════════════════════════════════════════════════════════════

html = rep(html,
    "  <div class=\"filtro-datas\">\n    <span style=\"font-size:12px;color:#64748b;margin-right:4px\">Periodo:</span>\n    <button class=\"btn-periodo\" onclick=\"selecionarPeriodo('google',this,7)\">7d</button>\n    <button class=\"btn-periodo\" onclick=\"selecionarPeriodo('google',this,14)\">14d</button>\n    <button class=\"btn-periodo ativo\" id=\"googleBtnAtivo\" onclick=\"selecionarPeriodo('google',this,30)\">30d</button>\n    <button class=\"btn-periodo\" onclick=\"selecionarPeriodo('google',this,90)\">90d</button>\n    <div class=\"div-sep-v\"></div>\n    <input type=\"date\" id=\"googleDataInicio\" class=\"input-data\">\n    <span style=\"color:#64748b;font-size:12px\">—</span>\n    <input type=\"date\" id=\"googleDataFim\" class=\"input-data\">\n    <button class=\"btn-aplicar\" onclick=\"aplicarFiltroCustom('google')\">Aplicar</button>\n    <span id=\"googlePeriodoLabel\" style=\"font-size:11px;color:#64748b;margin-left:6px\">Exibindo: ultimos 30 dias</span>\n  </div>",
    "",
    'Remover filtro per-tab Google'
)

# ════════════════════════════════════════════════════════════
# 4. Adicionar IDs a elementos KPI — Visão Geral
# ════════════════════════════════════════════════════════════

html = rep(html,
    '<div class="kpi-label">Total Investido (30d)</div>\n      <div class="kpi-valor">R$ 49.259</div>',
    '<div class="kpi-label" id="kpiLabelInvestido">Total Investido (30d)</div>\n      <div class="kpi-valor" id="kpiTotalInvestido">R$ 49.259</div>',
    'ID kpiTotalInvestido'
)

html = rep(html,
    '<div class="kpi-label">Valor Gerado Google</div>\n      <div class="kpi-valor">R$ 46.704</div>\n      <div class="kpi-sub">ROAS 2,56x</div>',
    '<div class="kpi-label">Valor Gerado Google</div>\n      <div class="kpi-valor" id="kpiValorGoogle">R$ 46.704</div>\n      <div class="kpi-sub">ROAS 2,56x</div>',
    'ID kpiValorGoogle'
)

html = rep(html,
    '<div class="kpi-label">Sessoes no Site (30d)</div>\n      <div class="kpi-valor">111.574</div>',
    '<div class="kpi-label" id="kpiLabelSessoes">Sessoes no Site (30d)</div>\n      <div class="kpi-valor" id="kpiSessoes">111.574</div>',
    'ID kpiSessoes'
)

html = rep(html,
    '<div class="kpi-sub">166.425 cliques</div>',
    '<div class="kpi-sub" id="kpiCpcSub">166.425 cliques</div>',
    'ID kpiCpcSub'
)

# ════════════════════════════════════════════════════════════
# 5. Adicionar IDs a KPIs do Meta Ads
# ════════════════════════════════════════════════════════════

html = rep(html,
    '<div class="kpi-label">Total Gasto (30d)</div>\n      <div class="kpi-valor">R$ 31.007</div>',
    '<div class="kpi-label" id="kpiLabelMetaGasto">Total Gasto (30d)</div>\n      <div class="kpi-valor" id="kpiMetaGasto">R$ 31.007</div>',
    'ID kpiMetaGasto'
)

html = rep(html,
    '<div class="kpi-label">Impressoes</div>\n      <div class="kpi-valor">4,67M</div>',
    '<div class="kpi-label">Impressoes</div>\n      <div class="kpi-valor" id="kpiMetaImpressoes">4,67M</div>',
    'ID kpiMetaImpressoes'
)

html = rep(html,
    '<div class="kpi-label">Cliques Totais</div>\n      <div class="kpi-valor">166.425</div>',
    '<div class="kpi-label">Cliques Totais</div>\n      <div class="kpi-valor" id="kpiMetaCliques">166.425</div>',
    'ID kpiMetaCliques'
)

# ════════════════════════════════════════════════════════════
# 6. Adicionar IDs a KPIs do Google Ads
# ════════════════════════════════════════════════════════════

html = rep(html,
    '<div class="kpi-label">Total Gasto (30d)</div>\n      <div class="kpi-valor">R$ 18.251</div>',
    '<div class="kpi-label" id="kpiLabelGoogleGasto">Total Gasto (30d)</div>\n      <div class="kpi-valor" id="kpiGoogleGasto">R$ 18.251</div>',
    'ID kpiGoogleGasto'
)

html = rep(html,
    '<div class="kpi-label">Valor de Conversao</div>\n      <div class="kpi-valor">R$ 46.704</div>',
    '<div class="kpi-label">Valor de Conversao</div>\n      <div class="kpi-valor" id="kpiGoogleValorConv">R$ 46.704</div>',
    'ID kpiGoogleValorConv'
)

html = rep(html,
    '<div class="kpi-label">Conversoes</div>\n      <div class="kpi-valor">891</div>',
    '<div class="kpi-label">Conversoes</div>\n      <div class="kpi-valor" id="kpiGoogleConversoes">891</div>',
    'ID kpiGoogleConversoes'
)

html = rep(html,
    '<div class="kpi-label">Cliques</div>\n      <div class="kpi-valor">8.043</div>',
    '<div class="kpi-label">Cliques</div>\n      <div class="kpi-valor" id="kpiGoogleCliques">8.043</div>',
    'ID kpiGoogleCliques'
)

html = rep(html,
    '<div class="kpi-label">Impressoes</div>\n      <div class="kpi-valor">922.965</div>',
    '<div class="kpi-label">Impressoes</div>\n      <div class="kpi-valor" id="kpiGoogleImpressoes">922.965</div>',
    'ID kpiGoogleImpressoes'
)

# ════════════════════════════════════════════════════════════
# 7. Adicionar IDs a KPIs do Analytics
# ════════════════════════════════════════════════════════════

html = rep(html,
    '<div class="kpi-label">Sessoes Totais (30d)</div>\n      <div class="kpi-valor">111.574</div>',
    '<div class="kpi-label" id="kpiLabelGASessoes">Sessoes Totais (30d)</div>\n      <div class="kpi-valor" id="kpiGASessoes">111.574</div>',
    'ID kpiGASessoes'
)

html = rep(html,
    '<div class="kpi-label">Usuarios Totais</div>\n      <div class="kpi-valor">109.522</div>',
    '<div class="kpi-label">Usuarios Totais</div>\n      <div class="kpi-valor" id="kpiGAUsuarios">109.522</div>',
    'ID kpiGAUsuarios'
)

html = rep(html,
    '<div class="kpi-label">Novos Usuarios</div>\n      <div class="kpi-valor">107.530</div>',
    '<div class="kpi-label">Novos Usuarios</div>\n      <div class="kpi-valor" id="kpiGANovos">107.530</div>',
    'ID kpiGANovos'
)

html = rep(html,
    '<div class="kpi-label">Pageviews</div>\n      <div class="kpi-valor">151.342</div>',
    '<div class="kpi-label">Pageviews</div>\n      <div class="kpi-valor" id="kpiGAPageviews">151.342</div>',
    'ID kpiGAPageviews'
)

# ════════════════════════════════════════════════════════════
# 8. Inserir bloco JS — FILTRO GLOBAL — antes de renderizarVisaoGeral
# ════════════════════════════════════════════════════════════

FILTRO_JS = """\
// ────────────────────────────────────────────────────────────────────────────
// FILTRO GLOBAL DE DATA
// Controla todas as abas: escala dados de Meta/Google/Analytics pelo fator
// dias/30. Para Rezdy usa o filtro de horarioVoo ja existente.
// ────────────────────────────────────────────────────────────────────────────

const FILTRO = { dias: 30, ini: null, fim: null };

function fatorEscala() { return FILTRO.dias / 30; }

function fmtMilloes(v) {
  if(v >= 1e6) return (v/1e6).toFixed(2).replace('.',',')+'M';
  return formatarNumero(Math.round(v));
}

function aplicarFiltroGlobal(dias, btn) {
  FILTRO.dias = dias;
  FILTRO.ini = null;
  FILTRO.fim = null;
  document.querySelectorAll("#filtroGlobal .btn-periodo").forEach(b=>b.classList.remove("ativo"));
  if(btn) btn.classList.add("ativo");
  const lbl = document.getElementById("globalPeriodoLabel");
  if(lbl) lbl.textContent = "Exibindo: ultimos " + dias + " dias";
  reRenderAbaAtiva();
}

function aplicarFiltroGlobalCustom() {
  const ini = document.getElementById("globalDataInicio").value;
  const fim = document.getElementById("globalDataFim").value;
  if(!ini||!fim){ alert("Selecione data de inicio e fim."); return; }
  const msIni = new Date(ini).getTime();
  const msFim = new Date(fim).getTime();
  const dias = Math.max(1, Math.round((msFim-msIni)/86400000)+1);
  FILTRO.dias = dias;
  FILTRO.ini = new Date(ini); FILTRO.ini.setHours(0,0,0,0);
  FILTRO.fim = new Date(fim); FILTRO.fim.setHours(23,59,59,999);
  document.querySelectorAll("#filtroGlobal .btn-periodo").forEach(b=>b.classList.remove("ativo"));
  const lbl = document.getElementById("globalPeriodoLabel");
  if(lbl) lbl.textContent = "Exibindo: "+ini+" a "+fim+" ("+dias+" dias)";
  reRenderAbaAtiva();
}

function reRenderAbaAtiva() {
  const aba = document.querySelector(".conteudo.ativo");
  if(!aba) return;
  const id = aba.id;
  try {
    if(id==="visaoGeral")        renderizarVisaoGeral();
    else if(id==="midiaPage")    renderizarMetaAds();
    else if(id==="googleAdsPage")renderizarGoogleAds();
    else if(id==="analyticsPage")renderizarAnalytics();
    else if(id==="rezdyPage")    carregarRezdy();
    else if(id==="passageirosPage")renderizarPassageiros();
  } catch(e){ console.error("reRenderAbaAtiva:",e); }
  // Sempre atualiza KPIs da visao geral se nao for ela a aba ativa
  if(id!=="visaoGeral") {
    try { atualizarKpisGeral(); } catch(e){}
  }
}

function atualizarKpisGeral() {
  const f = fatorEscala();
  const totalInv = (DADOS_META.totalGasto + DADOS_GOOGLE.totalGasto) * f;
  const el1 = document.getElementById("kpiTotalInvestido");
  if(el1) el1.textContent = "R$ " + formatarNumero(Math.round(totalInv));
  const el2 = document.getElementById("kpiValorGoogle");
  if(el2) el2.textContent = "R$ " + formatarNumero(Math.round(DADOS_GOOGLE.totalValorConv*f));
  const el3 = document.getElementById("kpiSessoes");
  if(el3) el3.textContent = formatarNumero(Math.round(DADOS_GA.totalSessoes*f));
  const el4 = document.getElementById("kpiCpcSub");
  if(el4) el4.textContent = formatarNumero(Math.round(DADOS_META.totalCliques*f))+" cliques";
  const lbl1 = document.getElementById("kpiLabelInvestido");
  if(lbl1) lbl1.textContent = "Total Investido ("+FILTRO.dias+"d)";
  const lbl3 = document.getElementById("kpiLabelSessoes");
  if(lbl3) lbl3.textContent = "Sessoes no Site ("+FILTRO.dias+"d)";
}

"""

html = rep(html,
    'function renderizarVisaoGeral() { try {',
    FILTRO_JS + 'function renderizarVisaoGeral() { try {',
    'Inserir bloco FILTRO JS'
)

# ════════════════════════════════════════════════════════════
# 9. Adicionar atualizacao de KPIs ao final de renderizarVisaoGeral
# ════════════════════════════════════════════════════════════

GERAL_KPI_UPDATE = """\
  // Atualiza KPIs com fator de escala do filtro global
  atualizarKpisGeral();
} catch(e){ console.error("renderizarVisaoGeral:",e); }}"""

html = rep(html,
    "} catch(e){ console.error(\"renderizarVisaoGeral:\",e); }}",
    GERAL_KPI_UPDATE,
    'Adicionar atualizarKpisGeral em renderizarVisaoGeral'
)

# ════════════════════════════════════════════════════════════
# 10. Adicionar atualizacao de KPIs ao final de renderizarMetaAds
# ════════════════════════════════════════════════════════════

META_KPI_UPDATE = """\
  // Atualiza KPIs com fator de escala
  { const f=fatorEscala();
    const elMG=document.getElementById("kpiMetaGasto");
    if(elMG) elMG.textContent="R$ "+formatarNumero(Math.round(DADOS_META.totalGasto*f));
    const elMI=document.getElementById("kpiMetaImpressoes");
    if(elMI) elMI.textContent=fmtMilloes(DADOS_META.totalImpressoes*f);
    const elMC=document.getElementById("kpiMetaCliques");
    if(elMC) elMC.textContent=formatarNumero(Math.round(DADOS_META.totalCliques*f));
    const lbl=document.getElementById("kpiLabelMetaGasto");
    if(lbl) lbl.textContent="Total Gasto ("+FILTRO.dias+"d)";
  }
} catch(e){ console.error("renderizarMetaAds:",e); }}"""

html = rep(html,
    "} catch(e){ console.error(\"renderizarMetaAds:\",e); }}",
    META_KPI_UPDATE,
    'Adicionar KPI update em renderizarMetaAds'
)

# ════════════════════════════════════════════════════════════
# 11. Adicionar atualizacao de KPIs ao final de renderizarGoogleAds
# ════════════════════════════════════════════════════════════

GOOGLE_KPI_UPDATE = """\
  // Atualiza KPIs com fator de escala
  { const f=fatorEscala();
    const elGG=document.getElementById("kpiGoogleGasto");
    if(elGG) elGG.textContent="R$ "+formatarNumero(Math.round(DADOS_GOOGLE.totalGasto*f));
    const elGV=document.getElementById("kpiGoogleValorConv");
    if(elGV) elGV.textContent="R$ "+formatarNumero(Math.round(DADOS_GOOGLE.totalValorConv*f));
    const elGC=document.getElementById("kpiGoogleConversoes");
    if(elGC) elGC.textContent=formatarNumero(Math.round(DADOS_GOOGLE.totalConversoes*f));
    const elGCl=document.getElementById("kpiGoogleCliques");
    if(elGCl) elGCl.textContent=formatarNumero(Math.round(DADOS_GOOGLE.totalCliques*f));
    const totImpG=DADOS_GOOGLE.campanhas.reduce((s,c)=>s+(c.impressoes||0),0);
    const elGI=document.getElementById("kpiGoogleImpressoes");
    if(elGI) elGI.textContent=formatarNumero(Math.round(totImpG*f));
    const lbl=document.getElementById("kpiLabelGoogleGasto");
    if(lbl) lbl.textContent="Total Gasto ("+FILTRO.dias+"d)";
  }
} catch(e){ console.error("renderizarGoogleAds:",e); }}"""

html = rep(html,
    "} catch(e){ console.error(\"renderizarGoogleAds:\",e); }}",
    GOOGLE_KPI_UPDATE,
    'Adicionar KPI update em renderizarGoogleAds'
)

# ════════════════════════════════════════════════════════════
# 12. Adicionar atualizacao de KPIs ao final de renderizarAnalytics
# (sem try/catch atualmente — adicionar wrapper e update)
# ════════════════════════════════════════════════════════════

ANALYTICS_KPI_UPDATE = """\
  // Atualiza KPIs com fator de escala
  { const f=fatorEscala();
    const elGAS=document.getElementById("kpiGASessoes");
    if(elGAS) elGAS.textContent=formatarNumero(Math.round(DADOS_GA.totalSessoes*f));
    const totU=DADOS_GA.canais.reduce((s,c)=>s+c.usuarios,0);
    const elGAU=document.getElementById("kpiGAUsuarios");
    if(elGAU) elGAU.textContent=formatarNumero(Math.round(totU*f));
    const totN=DADOS_GA.canais.reduce((s,c)=>s+c.novos,0);
    const elGAN=document.getElementById("kpiGANovos");
    if(elGAN) elGAN.textContent=formatarNumero(Math.round(totN*f));
    const totV=DADOS_GA.canais.reduce((s,c)=>s+c.views,0);
    const elGAV=document.getElementById("kpiGAPageviews");
    if(elGAV) elGAV.textContent=formatarNumero(Math.round(totV*f));
    const lbl=document.getElementById("kpiLabelGASessoes");
    if(lbl) lbl.textContent="Sessoes Totais ("+FILTRO.dias+"d)";
  }
}
"""

# renderizarAnalytics ends with just closing brace of the outer function
# Find: end of the table rendering, then the closing brace
html = rep(html,
    "    </tr>`).join(\"\");\n}\n\n// ────────────────────────────────────────────────────────────────────────────\n// ABA: REZDY",
    "    </tr>`).join(\"\");\n" + ANALYTICS_KPI_UPDATE + "\n// ────────────────────────────────────────────────────────────────────────────\n// ABA: REZDY",
    'Adicionar KPI update em renderizarAnalytics'
)

# ════════════════════════════════════════════════════════════
# Salvar
# ════════════════════════════════════════════════════════════

print(f"\n  Total de alteracoes: {changes}/12 esperadas")

with open(ARQUIVO, "w", encoding='utf-8') as f:
    f.write(html)

print(f"  Arquivo salvo: {ARQUIVO}")
print(f"  Tamanho: {len(html):,} chars")

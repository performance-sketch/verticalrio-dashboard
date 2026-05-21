"""
adicionar_drag_meta.py
1. Adiciona card "Investimento Meta" na Visao Geral
2. Garante que todos os cards da visao geral respondem ao filtro de data
3. Implementa drag-and-drop para reordenar cards
"""

ARQUIVO = r'C:\Users\info\rezdy-dashboard\dashboard_completo.html'

with open(ARQUIVO, encoding='utf-8') as f:
    html = f.read()

ok = 0

def rep(content, old, new, desc):
    global ok
    count = content.count(old)
    if count == 0:
        print(f"  [NAO ENCONTRADO] {desc}")
        return content
    if count > 1:
        print(f"  [MULTIPLOS {count}] {desc}")
    result = content.replace(old, new, 1)
    ok += 1
    print(f"  OK: {desc}")
    return result

# ═══════════════════════════════════════════════════════════════
# 1. CSS — drag-and-drop
# ═══════════════════════════════════════════════════════════════

CSS_DRAG = """\
    /* ── DRAG & DROP ── */
    .card-kpi[draggable=true],.card[draggable=true]{cursor:grab;transition:opacity .15s,transform .15s,border-color .15s,box-shadow .15s}
    .card-kpi[draggable=true]:active,.card[draggable=true]:active{cursor:grabbing}
    .card-kpi.arrastando,.card.arrastando{opacity:.3;transform:scale(.96);border-style:dashed}
    .card-kpi.drag-sobre,.card.drag-sobre{border-color:#5a7fff!important;box-shadow:0 0 0 2px rgba(90,127,255,.35)!important}
    .drag-hint{position:absolute;top:6px;right:8px;font-size:11px;color:#1e2540;opacity:0;transition:opacity .2s;pointer-events:none;letter-spacing:1px}
    .card-kpi:hover .drag-hint,.card:hover .drag-hint{opacity:1;color:#475569}
  </style>"""

html = rep(html, '  </style>', CSS_DRAG, 'CSS drag-and-drop')

# ═══════════════════════════════════════════════════════════════
# 2. HTML — novo card "Investimento Meta" na grade-kpi de visaoGeral
#    + drag-hint em todos os cards da grade-kpi
# ═══════════════════════════════════════════════════════════════

NOVO_GRADE_KPI = """\
  <div class="grade-kpi" id="kpiGeral">
    <div class="card-kpi kpi-azul" draggable="true">
      <span class="drag-hint">&#x2B1D;&#x2B1D;</span>
      <div class="kpi-label" id="kpiLabelInvestido">Total Investido (30d)</div>
      <div class="kpi-valor" id="kpiTotalInvestido">R$ 49.259</div>
      <div class="kpi-sub">Meta + Google Ads</div>
    </div>
    <div class="card-kpi kpi-rosa" draggable="true">
      <span class="drag-hint">&#x2B1D;&#x2B1D;</span>
      <div class="kpi-label" id="kpiLabelMetaInvest">Investimento Meta (30d)</div>
      <div class="kpi-valor" id="kpiMetaInvestGeral">R$ 31.007</div>
      <div class="kpi-sub">Meta Ads</div>
    </div>
    <div class="card-kpi kpi-verde" draggable="true">
      <span class="drag-hint">&#x2B1D;&#x2B1D;</span>
      <div class="kpi-label">Valor Gerado Google</div>
      <div class="kpi-valor" id="kpiValorGoogle">R$ 46.704</div>
      <div class="kpi-sub">ROAS 2,56x</div>
    </div>
    <div class="card-kpi kpi-roxo" draggable="true">
      <span class="drag-hint">&#x2B1D;&#x2B1D;</span>
      <div class="kpi-label" id="kpiLabelSessoes">Sessoes no Site (30d)</div>
      <div class="kpi-valor" id="kpiSessoes">111.574</div>
      <div class="kpi-sub">GA4 &#x2014; Vertical Rio</div>
    </div>
    <div class="card-kpi kpi-laranja" id="kpiReservas" draggable="true">
      <span class="drag-hint">&#x2B1D;&#x2B1D;</span>
      <div class="kpi-label">Reservas Ativas</div>
      <div class="kpi-valor" id="totalReservasGeral">--</div>
      <div class="kpi-sub">Rezdy ao vivo</div>
    </div>
    <div class="card-kpi kpi-amarelo" id="kpiReceita" draggable="true">
      <span class="drag-hint">&#x2B1D;&#x2B1D;</span>
      <div class="kpi-label">Receita Rezdy</div>
      <div class="kpi-valor" id="receitaGeralRezdy">--</div>
      <div class="kpi-sub">Ultimas 100 reservas</div>
    </div>
    <div class="card-kpi kpi-ciano" draggable="true">
      <span class="drag-hint">&#x2B1D;&#x2B1D;</span>
      <div class="kpi-label">CPC Medio Meta</div>
      <div class="kpi-valor">R$ 0,19</div>
      <div class="kpi-sub" id="kpiCpcSub">166.425 cliques</div>
    </div>
  </div>"""

OLD_GRADE_KPI = """\
  <div class="grade-kpi" id="kpiGeral">
    <div class="card-kpi kpi-azul">
      <div class="kpi-label" id="kpiLabelInvestido">Total Investido (30d)</div>
      <div class="kpi-valor" id="kpiTotalInvestido">R$ 49.259</div>
      <div class="kpi-sub">Meta + Google Ads</div>
    </div>
    <div class="card-kpi kpi-verde">
      <div class="kpi-label">Valor Gerado Google</div>
      <div class="kpi-valor" id="kpiValorGoogle">R$ 46.704</div>
      <div class="kpi-sub">ROAS 2,56x</div>
    </div>
    <div class="card-kpi kpi-roxo">
      <div class="kpi-label" id="kpiLabelSessoes">Sessoes no Site (30d)</div>
      <div class="kpi-valor" id="kpiSessoes">111.574</div>
      <div class="kpi-sub">GA4 &#x2014; Vertical Rio</div>
    </div>
    <div class="card-kpi kpi-laranja" id="kpiReservas">
      <div class="kpi-label">Reservas Ativas</div>
      <div class="kpi-valor" id="totalReservasGeral">--</div>
      <div class="kpi-sub">Rezdy ao vivo</div>
    </div>
    <div class="card-kpi kpi-amarelo" id="kpiReceita">
      <div class="kpi-label">Receita Rezdy</div>
      <div class="kpi-valor" id="receitaGeralRezdy">--</div>
      <div class="kpi-sub">Ultimas 100 reservas</div>
    </div>
    <div class="card-kpi kpi-ciano">
      <div class="kpi-label">CPC Medio Meta</div>
      <div class="kpi-valor">R$ 0,19</div>
      <div class="kpi-sub" id="kpiCpcSub">166.425 cliques</div>
    </div>
  </div>"""

html = rep(html, OLD_GRADE_KPI, NOVO_GRADE_KPI, 'Novo grade-kpi com Meta invest e draggable')

# ═══════════════════════════════════════════════════════════════
# 3. HTML — adicionar draggable + drag-hint aos cards de grafico
#    na visaoGeral (grade-3 e grade-21)
# ═══════════════════════════════════════════════════════════════

html = rep(html,
    '  <div class="grade-3">\n    <div class="card">\n      <div class="card-titulo">Trafego por Canal',
    '  <div class="grade-3">\n    <div class="card" draggable="true"><span class="drag-hint">&#x2B1D;&#x2B1D;</span>\n      <div class="card-titulo">Trafego por Canal',
    'draggable trafego'
)

html = rep(html,
    '    <div class="card">\n      <div class="card-titulo">Gasto em Anuncios',
    '    <div class="card" draggable="true"><span class="drag-hint">&#x2B1D;&#x2B1D;</span>\n      <div class="card-titulo">Gasto em Anuncios',
    'draggable gasto'
)

html = rep(html,
    '    <div class="card">\n      <div class="card-titulo">Status Reservas Rezdy',
    '    <div class="card" draggable="true"><span class="drag-hint">&#x2B1D;&#x2B1D;</span>\n      <div class="card-titulo">Status Reservas Rezdy',
    'draggable status rezdy'
)

html = rep(html,
    '  <div class="grade-21">\n    <div class="card">\n      <div class="card-titulo">Campanhas Meta Ads',
    '  <div class="grade-21">\n    <div class="card" draggable="true"><span class="drag-hint">&#x2B1D;&#x2B1D;</span>\n      <div class="card-titulo">Campanhas Meta Ads',
    'draggable campanhas meta'
)

html = rep(html,
    '    <div class="card">\n      <div class="card-titulo">Google Ads &#x2014; ROAS por Campanha',
    '    <div class="card" draggable="true"><span class="drag-hint">&#x2B1D;&#x2B1D;</span>\n      <div class="card-titulo">Google Ads &#x2014; ROAS por Campanha',
    'draggable roas google'
)

# ═══════════════════════════════════════════════════════════════
# 4. JS — atualizar atualizarKpisGeral para incluir Meta invest
# ═══════════════════════════════════════════════════════════════

OLD_ATUALIZAR = """\
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
}"""

NEW_ATUALIZAR = """\
function atualizarKpisGeral() {
  const f = fatorEscala();
  const totalInv = (DADOS_META.totalGasto + DADOS_GOOGLE.totalGasto) * f;
  const el1 = document.getElementById("kpiTotalInvestido");
  if(el1) el1.textContent = "R$ " + formatarNumero(Math.round(totalInv));
  const elMeta = document.getElementById("kpiMetaInvestGeral");
  if(elMeta) elMeta.textContent = "R$ " + formatarNumero(Math.round(DADOS_META.totalGasto*f));
  const el2 = document.getElementById("kpiValorGoogle");
  if(el2) el2.textContent = "R$ " + formatarNumero(Math.round(DADOS_GOOGLE.totalValorConv*f));
  const el3 = document.getElementById("kpiSessoes");
  if(el3) el3.textContent = formatarNumero(Math.round(DADOS_GA.totalSessoes*f));
  const el4 = document.getElementById("kpiCpcSub");
  if(el4) el4.textContent = formatarNumero(Math.round(DADOS_META.totalCliques*f))+" cliques";
  const lbl1 = document.getElementById("kpiLabelInvestido");
  if(lbl1) lbl1.textContent = "Total Investido ("+FILTRO.dias+"d)";
  const lblMeta = document.getElementById("kpiLabelMetaInvest");
  if(lblMeta) lblMeta.textContent = "Investimento Meta ("+FILTRO.dias+"d)";
  const lbl3 = document.getElementById("kpiLabelSessoes");
  if(lbl3) lbl3.textContent = "Sessoes no Site ("+FILTRO.dias+"d)";
}"""

html = rep(html, OLD_ATUALIZAR, NEW_ATUALIZAR, 'Atualizar atualizarKpisGeral com Meta invest')

# ═══════════════════════════════════════════════════════════════
# 5. JS — funcao initDragDrop + habilitarDrag
# ═══════════════════════════════════════════════════════════════

DRAG_JS = """\
// ────────────────────────────────────────────────────────────────────────────
// DRAG & DROP — reordenar cards dentro de cada grade
// ────────────────────────────────────────────────────────────────────────────

function initDragDrop() {
  const grids = document.querySelectorAll('.grade-kpi,.grade-2,.grade-3,.grade-21,.grade-12');
  grids.forEach(grid => {
    let src = null;

    grid.addEventListener('dragstart', e => {
      const card = e.target.closest('.card-kpi,.card');
      if(!card || !grid.contains(card)) return;
      src = card;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain','');
      setTimeout(() => { if(src) src.classList.add('arrastando'); }, 0);
    });

    grid.addEventListener('dragend', () => {
      if(src) src.classList.remove('arrastando');
      grid.querySelectorAll('.drag-sobre').forEach(c => c.classList.remove('drag-sobre'));
      src = null;
    });

    grid.addEventListener('dragover', e => {
      e.preventDefault();
      const tgt = e.target.closest('.card-kpi,.card');
      if(!tgt || !grid.contains(tgt) || tgt === src) return;
      grid.querySelectorAll('.drag-sobre').forEach(c => c.classList.remove('drag-sobre'));
      tgt.classList.add('drag-sobre');
    });

    grid.addEventListener('dragleave', e => {
      if(!grid.contains(e.relatedTarget)) {
        grid.querySelectorAll('.drag-sobre').forEach(c => c.classList.remove('drag-sobre'));
      }
    });

    grid.addEventListener('drop', e => {
      e.preventDefault();
      const tgt = e.target.closest('.card-kpi,.card');
      if(!tgt || !grid.contains(tgt) || tgt === src || !src) return;
      tgt.classList.remove('drag-sobre');
      const rect = tgt.getBoundingClientRect();
      // Para grade-kpi (horizontal) usa X; para listas verticais usa Y
      const useX = grid.classList.contains('grade-kpi');
      const after = useX ? e.clientX > rect.left + rect.width/2
                         : e.clientY > rect.top  + rect.height/2;
      grid.insertBefore(src, after ? tgt.nextSibling : tgt);
    });
  });
}

function habilitarDrag() {
  document.querySelectorAll('.grade-kpi .card-kpi, .grade-2 .card, .grade-3 .card, .grade-21 .card, .grade-12 .card').forEach(c => {
    if(!c.getAttribute('draggable')) {
      c.setAttribute('draggable','true');
      if(!c.querySelector('.drag-hint')) {
        const hint = document.createElement('span');
        hint.className = 'drag-hint';
        hint.innerHTML = '&#x2B1D;&#x2B1D;';
        c.insertBefore(hint, c.firstChild);
      }
    }
  });
}

"""

html = rep(html,
    'function inicializarDashboard() {',
    DRAG_JS + 'function inicializarDashboard() {',
    'Inserir initDragDrop e habilitarDrag'
)

# ═══════════════════════════════════════════════════════════════
# 6. Chamar initDragDrop + habilitarDrag na inicializacao
# ═══════════════════════════════════════════════════════════════

html = rep(html,
    'function inicializarDashboard() {\n  try { renderizarVisaoGeral(); }    catch(e){ console.error("visaoGeral:",e); }\n  try { renderizarResumoRezdy(); }   catch(e){ console.error("resumoRezdy:",e); }',
    'function inicializarDashboard() {\n  try { renderizarVisaoGeral(); }    catch(e){ console.error("visaoGeral:",e); }\n  try { renderizarResumoRezdy(); }   catch(e){ console.error("resumoRezdy:",e); }\n  initDragDrop();\n  habilitarDrag();',
    'Chamar initDragDrop na inicializacao'
)

# Tambem chamar habilitarDrag apos reRenderAbaAtiva
html = rep(html,
    "  } catch(e){ console.error(\"reRenderAbaAtiva:\",e); }\n  // Sempre atualiza KPIs da visao geral se nao for ela a aba ativa",
    "  } catch(e){ console.error(\"reRenderAbaAtiva:\",e); }\n  habilitarDrag();\n  // Sempre atualiza KPIs da visao geral se nao for ela a aba ativa",
    'Chamar habilitarDrag apos reRender'
)

# ═══════════════════════════════════════════════════════════════
# Salvar
# ═══════════════════════════════════════════════════════════════

print(f"\n  Total alteracoes: {ok}/10 esperadas")

with open(ARQUIVO, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"  Arquivo salvo — {len(html):,} chars")

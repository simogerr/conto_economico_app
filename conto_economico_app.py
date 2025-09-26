# conto_economico_app.py
from flask import Flask, render_template_string, request, send_file, redirect, url_for
import io
import pandas as pd

app = Flask(__name__)

# -------------------- utility numeri --------------------
def parse_num(value, default=0.0):
    if value is None:
        return default
    value = str(value).strip().replace(" ", "").replace(",", ".")
    try:
        return float(value)
    except:
        return default

# -------------------- template HTML --------------------
HTML = """
<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Calcolo Conto Economico</title>
<style>
  :root{ --bg:#0f172a; --card:#111827; --muted:#94a3b8; --accent:#22c55e; --txt:#e5e7eb; --ring:#374151; }
  body{ margin:0; background:linear-gradient(180deg,#0b1023,#0e1227 40%,#0f172a); color:var(--txt);
        font-family:system-ui,-apple-system,Segoe UI,Roboto,Inter,Helvetica,Arial }
  header{text-align:center;padding:16px}
  h1{margin:0;font-size:24px}
  .wrap{max-width:1100px;margin:0 auto;padding:20px}
  .card{background:rgba(17,24,39,.85);border:1px solid #1f2937;border-radius:14px;
        padding:16px;box-shadow:0 6px 20px rgba(0,0,0,.25);margin-bottom:16px}
  .card.results{background:#1e293b;} /* riepilogo blu più chiaro */

  /* Parent segmented control */
  .parent-tabs{display:flex;justify-content:center;margin:14px auto 0;flex-wrap:wrap}
  .segment{
    display:flex;gap:0;background:#0b1222;border:1px solid #1f2937;border-radius:12px;
    padding:4px;box-shadow:inset 0 0 0 1px #0b1222
  }
  .parent-btn{
    background:transparent;border:none;color:#94a3b8;font-weight:700;font-size:14px;
    padding:8px 14px;border-radius:8px;cursor:pointer;transition:all .2s
  }
  .parent-btn:hover{color:#e5e7eb}
  .parent-btn.active{
    background:#17243a;color:#e5e7eb;box-shadow:0 0 0 1px #243b55 inset
  }

  /* Child tabs */
  .tabs{display:flex;flex-wrap:wrap;justify-content:center;gap:30px;margin:12px 0 16px;border-bottom:2px solid #1f2937}
  .tablink{background:none;border:none;color:#94a3b8;font-weight:600;font-size:15px;
           padding:10px 0;cursor:pointer;position:relative;transition:color .25s}
  .tablink:hover{color:#e5e7eb}
  .tablink.active{color:var(--accent)}
  .tablink.active::after{content:"";position:absolute;bottom:-2px;left:0;right:0;height:3px;background:var(--accent);border-radius:2px}
  .tabcontent{display:none}

  .row{margin:8px 0;display:flex;gap:10px;align-items:center}
  .row label{flex:1}
  .row input, .row select{flex:1;padding:10px;border-radius:10px;border:1px solid var(--ring);background:#0b1023;color:var(--txt)}

  .actions{display:flex;gap:10px;justify-content:flex-end;margin-top:12px;flex-wrap:wrap}
  .btn{padding:8px 14px;border:none;border-radius:10px;cursor:pointer;font-weight:700;text-decoration:none;display:inline-block;text-align:center}
  .primary{background:linear-gradient(180deg,#16a34a,#15803d);color:#fff}
  .secondary{background:#0b1222;color:#e5e7eb;border:1px solid #1f2937}

  .pill{background:#0b1222;border:1px solid #1f2937;border-radius:12px;padding:10px;margin:6px 0}
  .pill.roi-good { background:#14532d; border:1px solid #15803d; color:#d1fae5; }

  .grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}

  .preview{margin-top:10px;padding:12px;border-radius:12px;background:#0b1222;border:1px solid #1f2937}
  .preview h4{margin:0 0 8px;font-size:14px;color:#cbd5e1}
  .preview .item{display:flex;justify-content:space-between;margin:4px 0;font-size:14px}
  .preview .item span:first-child{color:#a7b2c3}

  .muted{color:#94a3b8;font-size:13px}
</style>
</head>
<body>
<header>
  <h1>Calcolo Conto Economico</h1>
  <p>Strumento per analisi investimenti immobiliari</p>
</header>

<div class="wrap card">
  <!-- Parent tabs -->
  <div class="parent-tabs">
    <div class="segment">
      <button type="button" class="parent-btn" data-parent="compravendita" onclick="openParent('compravendita')">Compravendita</button>
      <button type="button" class="parent-btn" data-parent="affitti" onclick="openParent('affitti')">Affitti</button>
    </div>
  </div>
</div>

<!-- ========================== COMPRAVENDITA ========================== -->
<div class="wrap card parent-section" id="parent-compravendita">
  <form method="post" id="mainForm">
    <input type="hidden" id="parent_tab" name="parent_tab" value="{{ parent_tab or 'compravendita' }}"/>
    <input type="hidden" id="active_tab" name="active_tab" value="{{ active_tab or 'acquisto' }}"/>

    <div class="tabs">
      <button type="button" class="tablink" data-tab="acquisto"   onclick="openTab(event, 'acquisto')">Acquisto</button>
      <button type="button" class="tablink" data-tab="catastale"  onclick="openTab(event, 'catastale')">Valore Catastale & Registro</button>
      <button type="button" class="tablink" data-tab="vendita"    onclick="openTab(event, 'vendita')">Costi messa in vendita</button>
      <button type="button" class="tablink" data-tab="nuovoval"   onclick="openTab(event, 'nuovoval')">Nuovo Valore</button>
    </div>

    <!-- TAB: ACQUISTO -->
    <div id="acquisto" class="tabcontent">
      <div class="row"><label>Acquisto immobile</label><input type="text" name="ask" value="{{ formvals.ask }}"></div>
      <div class="row"><label>Imposta ipotecaria</label><input type="text" name="ipotecaria" value="{{ formvals.ipotecaria }}"></div>
      <div class="row"><label>Imposta catastale</label><input type="text" name="catastale" value="{{ formvals.catastale }}"></div>
      <div class="row"><label>Imposta di registro</label><input type="text" value="{{ formvals.imposta_registro }}" readonly></div>
      <div class="row"><label>Provvigioni agenzia (acquisto)</label><input type="text" name="agenzia" value="{{ formvals.agenzia }}"></div>
      <div class="row"><label>Studio architetto</label><input type="text" name="architetto" value="{{ formvals.architetto }}"></div>
      <div class="row"><label>Condono</label><input type="text" name="condono" value="{{ formvals.condono }}"></div>
      <div class="row"><label>Spese condominiali insolute</label><input type="text" name="condominio" value="{{ formvals.condominio }}"></div>
      <div class="row"><label>Nuove utenze (luce+gas)</label><input type="text" name="utenze" value="{{ formvals.utenze }}"></div>
      <div class="row"><label>Imprevisti</label><input type="text" name="imprevisti" value="{{ formvals.imprevisti }}"></div>

      <div class="row">
        <label>Tipo di ristrutturazione</label>
        <select name="ristrut_tipo">
          <option value="nessuna"   {% if formvals.ristrut_tipo=='nessuna' %}selected{% endif %}>Nessuna</option>
          <option value="piccola"   {% if formvals.ristrut_tipo=='piccola' %}selected{% endif %}>Piccoli interventi (10%)</option>
          <option value="intermedia"{% if formvals.ristrut_tipo=='intermedia' %}selected{% endif %}>Ristrutturazione intermedia (20%)</option>
          <option value="complessa" {% if formvals.ristrut_tipo=='complessa' %}selected{% endif %}>Ristrutturazione complessa (60%)</option>
        </select>
      </div>
      <div class="row"><label>Costo ristrutturazione (calcolato)</label><input type="text" value="{{ formvals.ristrutturazione }}" readonly></div>

      <div class="actions">
        <button class="btn primary" type="submit">Calcola</button>
        <a href="{{ url_for('reset') }}" class="btn secondary">Reset</a>
      </div>
    </div>

    <!-- (le altre tab rimangono uguali alla versione precedente) -->
    <!-- ... -->
  </form>
</div>

{% if results %}
<div class="wrap card results" id="riepilogo-compravendita">
  <h2>Riepilogo</h2>
  <div class="grid3">
    <div class="pill"><b>Tipo proprietà:</b> {{ results.tipo_label }}</div>
    <div class="pill"><b>Valore catastale:</b> {{ results.valore_catastale }}</div>
    <div class="pill"><b>Imposta di registro:</b> {{ results.imposta_registro }}</div>
    <div class="pill"><b>Costo ristrutturazione:</b> {{ results.ristrutturazione }}</div>
    <div class="pill"><b>Totale costi acquisto:</b> {{ results.totale_acquisto }}</div>
    <div class="pill"><b>Costi messa in vendita:</b> {{ results.costi_vendita }}</div>
    <div class="pill"><b>Valore finale percepito:</b> {{ results.valore_finale }}</div>
    <div class="pill {{ results.roi_class }}"><b>ROI:</b> {{ results.roi }}</div>
  </div>
</div>
{% endif %}

<!-- ========================== AFFITTI (scaffolding) ========================== -->
<div class="wrap card parent-section" id="parent-affitti" style="display:none">
  <h2 style="margin-top:0">Affitti</h2>
  <p class="muted">Sezione in preparazione. Qui inseriremo canone, spese ricorrenti, tassazione cedolare, vacancy, ROI annuo, cashflow, ecc.</p>
</div>

<script>
/* ------- Parent tabs logic ------- */
function openParent(which){
  document.querySelectorAll(".parent-section").forEach(el=>el.style.display="none");
  document.querySelectorAll(".parent-btn").forEach(el=>el.classList.remove("active"));
  document.getElementById("parent-"+which).style.display="block";
  const btn=document.querySelector('.parent-btn[data-parent="'+which+'"]');
  if(btn) btn.classList.add("active");
  const hidden=document.getElementById("parent_tab");
  if(hidden) hidden.value=which;
}
</script>
</body>
</html>
"""

# (Il backend Python resta identico alla versione che già funziona, con ROI e Excel export.)
# -------------------- calcoli backend, routes ecc. --------------------
# ... (puoi ricollocare qui compute_results, index, download, reset come nel file precedente)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

from flask import Flask, render_template_string, request, send_file
import io
import pandas as pd

app = Flask(__name__)

# funzione per gestire i numeri con virgola o punto
def parse_num(value, default=0.0):
    if value is None:
        return default
    value = str(value).strip().replace(" ", "").replace(",", ".")
    try:
        return float(value)
    except:
        return default

HTML = """
<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Deal Checker Immobiliare</title>
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

  .tabs{display:flex;flex-wrap:wrap;justify-content:center;gap:30px;margin-bottom:16px;border-bottom:2px solid #1f2937}
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
  .btn{padding:8px 14px;border:none;border-radius:10px;cursor:pointer;font-weight:700}
  .primary{background:linear-gradient(180deg,#16a34a,#15803d);color:#fff}
  .secondary{background:#0b1222;color:#e5e7eb;border:1px solid #1f2937}

  .pill{background:#0b1222;border:1px solid #1f2937;border-radius:12px;padding:10px;margin:6px 0}
  .grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}

  .preview{margin-top:10px;padding:12px;border-radius:12px;background:#0b1222;border:1px solid #1f2937}
  .preview h4{margin:0 0 8px;font-size:14px;color:#cbd5e1}
  .preview .item{display:flex;justify-content:space-between;margin:4px 0;font-size:14px}
  .preview .item span:first-child{color:#a7b2c3}

  .notes{margin-top:10px;color:#e5e7eb}
  .notes b{color:#fff}
</style>
</head>
<body>
<header>
  <h1>Deal Checker Immobiliare</h1>
  <p>Conto economico compravendita</p>
</header>

<div class="wrap card">
  <form method="post" id="mainForm">
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
      <div class="actions"><button class="btn primary" type="submit">Calcola</button></div>
    </div>

    <!-- TAB: VALORE CATASTALE & REGISTRO -->
    <div id="catastale" class="tabcontent">
      <div class="row">
        <label>Tipo di proprietà</label>
        <select name="tipo" id="tipo" onchange="autoFillByTipo();updatePreviewCat();">
          <option value="prima"  {{ 'selected' if formvals.tipo=='prima' else '' }}>Prima casa</option>
          <option value="seconda"{{ 'selected' if formvals.tipo=='seconda' else '' }}>Seconda casa</option>
        </select>
      </div>
      <div class="row"><label>Rendita catastale</label><input type="text" id="rendita" name="rendita" value="{{ formvals.rendita }}" oninput="updatePreviewCat()"></div>
      <div class="row"><label>Coefficiente</label><input type="text" id="coeff" name="coeff" value="{{ formvals.coeff }}" oninput="updatePreviewCat()"></div>
      <div class="row"><label>Imposta di registro %</label><input type="text" id="imposta_pct" name="imposta_pct" value="{{ formvals.imposta_pct }}" oninput="updatePreviewCat()"></div>

      <div class="preview">
        <h4>Anteprima calcoli</h4>
        <div class="item"><span>Valore catastale</span><span id="pv_val_cat">—</span></div>
        <div class="item"><span>Imposta di registro</span><span id="pv_imp_reg">—</span></div>
      </div>
      <div class="actions"><button class="btn primary" type="submit">Calcola</button></div>
    </div>

    <!-- TAB: COSTI MESSA IN VENDITA -->
    <div id="vendita" class="tabcontent">
      <div class="row">
        <label>Home staging % (sul prezzo di vendita)</label>
        <select name="hs_percent" onchange="updatePreviewVendita()">
          <option value="1" {% if formvals.hs_percent=='1' %}selected{% endif %}>1%</option>
          <option value="2" {% if formvals.hs_percent=='2' %}selected{% endif %}>2%</option>
          <option value="3" {% if formvals.hs_percent=='3' %}selected{% endif %}>3%</option>
        </select>
      </div>
      <div class="row"><label>APE</label><input type="text" id="ape" name="ape" value="{{ formvals.ape }}" oninput="updatePreviewVendita()"></div>
      <div class="row"><label>DICO/DIRI</label><input type="text" id="dico" name="dico" value="{{ formvals.dico }}" oninput="updatePreviewVendita()"></div>
      <div class="row"><label>Provvigione agenzia vendita %</label><input type="text" id="provv_sale_pct" name="provv_sale_pct" value="{{ formvals.provv_sale_pct }}" oninput="updatePreviewVendita()"></div>
      <div class="row"><label>Imprevisti</label><input type="text" id="vendita_imprevisti" name="vendita_imprevisti" value="{{ formvals.vendita_imprevisti }}" oninput="updatePreviewVendita()"></div>

      <div class="preview">
        <h4>Anteprima costi messa in vendita</h4>
        <div class="item"><span>Home staging</span><span id="pv_hs_cost">—</span></div>
        <div class="item"><span>APE</span><span id="pv_ape">—</span></div>
        <div class="item"><span>DICO/DIRI</span><span id="pv_dico">—</span></div>
        <div class="item"><span>Provvigione agenzia</span><span id="pv_provv">—</span></div>
        <div class="item"><span>Imprevisti</span><span id="pv_vimp">—</span></div>
        <hr style="border:none;border-top:1px solid #1f2937;margin:6px 0"/>
        <div class="item"><b>Totale</b><b id="pv_tot_vendita">—</b></div>
      </div>
      <div class="actions"><button class="btn primary" type="submit">Calcola</button></div>
    </div>

    <!-- TAB: NUOVO VALORE -->
    <div id="nuovoval" class="tabcontent">
      <div class="row"><label>Street price (prezzo giusto di vendita)</label><input type="text" id="street_price" name="street_price" value="{{ formvals.street_price }}" oninput="updatePreviewVal()"></div>
      <div class="row"><label>Incremento Home Staging %</label><input type="text" id="inc_hs_pct" name="inc_hs_pct" value="{{ formvals.inc_hs_pct }}" oninput="updatePreviewVal()"></div>
      <div class="row"><label>Incremento da ristrutturazione %</label><input type="text" id="inc_ristr_pct" name="inc_ristr_pct" value="{{ formvals.inc_ristr_pct }}" oninput="updatePreviewVal()"></div>

      <div class="preview">
        <h4>Anteprima valore</h4>
        <div class="item"><span>Valore finale percepito</span><span id="pv_val_finale">—</span></div>
      </div>
      <div class="actions"><button class="btn primary" type="submit">Calcola</button></div>
    </div>
  </form>
</div>

{% if results %}
<div class="wrap card results">
  <h2>Riepilogo</h2>
  <div class="grid3">
    <div class="pill"><b>Tipo proprietà:</b> {{ results.tipo_label }}</div>
    <div class="pill"><b>Valore catastale:</b> {{ results.valore_catastale }}</div>
    <div class="pill"><b>Imposta di registro:</b> {{ results.imposta_registro }}</div>
    <div class="pill"><b>Costo ristrutturazione:</b> {{ results.ristrutturazione }}</div>
    <div class="pill"><b>Totale costi acquisto:</b> {{ results.totale_acquisto }}</div>
    <div class="pill"><b>Costi messa in vendita:</b> {{ results.costi_vendita }}</div>
    <div class="pill"><b>Valore finale percepito:</b> {{ results.valore_finale }}</div>
    <div class="pill"><b>ROI:</b> {{ results.roi }}</div>
  </div>
</div>
{% endif %}

<script>
function openTab(evt, tabName) {
  document.querySelectorAll(".tabcontent").forEach(el => el.style.display="none");
  document.querySelectorAll(".tablink").forEach(el => el.classList.remove("active"));
  document.getElementById(tabName).style.display="block";
  if (evt && evt.currentTarget) evt.currentTarget.classList.add("active");
  document.getElementById("active_tab").value = tabName;
}
function num(v){ if(!v) return 0; v=(""+v).replace(",","."); return parseFloat(v)||0; }
function fmt(n){ return Math.round(n).toLocaleString('it-IT'); }
function autoFillByTipo(){
  const tipo=document.getElementById('tipo').value;
  if(tipo==='prima'){document.getElementById('coeff').value="115.5";document.getElementById('imposta_pct').value="2";}
  else{document.getElementById('coeff').value="126";document.getElementById('imposta_pct').value="9";}
  updatePreviewCat();
}
function updatePreviewCat(){
  const r=num(document.getElementById('rendita').value);
  const c=num(document.getElementById('coeff').value);
  const p=num(document.getElementById('imposta_pct').value);
  const val=r*c; const imp=val*(p/100);
  document.getElementById('pv_val_cat').innerHTML=fmt(val);
  document.getElementById('pv_imp_reg').innerHTML=fmt(imp);
}
function updatePreviewVendita(){
  const sp=num(document.getElementById("street_price")?document.getElementById("street_price").value:0);
  const hsPercent=num(document.querySelector("[name='hs_percent']").value);
  const ape=num(document.getElementById("ape").value);
  const dico=num(document.getElementById("dico").value);
  const provvPct=num(document.getElementById("provv_sale_pct").value);
  const vimp=num(document.getElementById("vendita_imprevisti").value);
  const hsCost=sp*(hsPercent/100);
  const provv=sp*(provvPct/100);
  const totale=hsCost+ape+dico+provv+vimp;
  document.getElementById("pv_hs_cost").innerHTML=fmt(hsCost);
  document.getElementById("pv_ape").innerHTML=fmt(ape);
  document.getElementById("pv_dico").innerHTML=fmt(dico);
  document.getElementById("pv_provv").innerHTML=fmt(provv);
  document.getElementById("pv_vimp").innerHTML=fmt(vimp);
  document.getElementById("pv_tot_vendita").innerHTML=fmt(totale);
}
function updatePreviewVal(){
  const sp=num(document.getElementById('street_price').value);
  const incHS=num(document.getElementById('inc_hs_pct').value);
  const incR=num(document.getElementById('inc_ristr_pct').value);
  const valFinale = sp * (1 + incHS/100 + incR/100);
  document.getElementById('pv_val_finale').innerHTML=fmt(valFinale);
}
document.addEventListener('DOMContentLoaded',()=>{
  const initial="{{ active_tab or 'acquisto' }}";
  const btn=document.querySelector('.tablink[data-tab="'+initial+'"]');
  if(btn) btn.click(); else openTab(null,'acquisto');
  updatePreviewCat();
  updatePreviewVendita();
  updatePreviewVal();
});
</script>
</body>
</html>
"""

def compute_results(form):
    ask = parse_num(form.get("ask"))
    ipotecaria = parse_num(form.get("ipotecaria"))
    catastale_cost = parse_num(form.get("catastale"))
    agenzia = parse_num(form.get("agenzia"))
    architetto = parse_num(form.get("architetto"))
    condono = parse_num(form.get("condono"))
    condominio = parse_num(form.get("condominio"))
    utenze = parse_num(form.get("utenze"))
    imprevisti = parse_num(form.get("imprevisti"))
    ristrut_tipo = form.get("ristrut_tipo","nessuna")
    perc_map = {"nessuna":0,"piccola":0.10,"intermedia":0.20,"complessa":0.60}
    ristr_perc = perc_map.get(ristrut_tipo,0.0)
    ristrutturazione = ask * ristr_perc

    # Catastale & registro
    tipo = form.get("tipo","prima")
    rendita = parse_num(form.get("rendita"))
    coeff = parse_num(form.get("coeff"))
    imposta_pct = parse_num(form.get("imposta_pct"))
    valore_catastale = rendita * coeff
    imposta_registro = valore_catastale * (imposta_pct / 100.0)

    totale_acquisto = (ask + ipotecaria + catastale_cost + agenzia + architetto +
                       condono + condominio + utenze + imprevisti + ristrutturazione +
                       imposta_registro)

    # Vendita
    street_price = parse_num(form.get("street_price"))
    hs_percent = parse_num(form.get("hs_percent"))
    ape = parse_num(form.get("ape"))
    dico = parse_num(form.get("dico"))
    provv_sale_pct = parse_num(form.get("provv_sale_pct"))
    vendita_imprevisti = parse_num(form.get("vendita_imprevisti"))
    hs_cost = street_price * (hs_percent/100.0)
    provv_sale_cost = street_price * (provv_sale_pct/100.0)
    costi_vendita = hs_cost + ape + dico + provv_sale_cost + vendita_imprevisti

    # Nuovo valore
    inc_hs_pct = parse_num(form.get("inc_hs_pct"))
    inc_ristr_pct = parse_num(form.get("inc_ristr_pct"))
    valore_finale = street_price * (1 + inc_hs_pct/100.0 + inc_ristr_pct/100.0)

    # ROI
    roi = 0
    if totale_acquisto > 0:
        roi = (valore_finale - totale_acquisto) / totale_acquisto * 100

    results = {
        "tipo_label": "Prima casa" if tipo=="prima" else "Seconda casa",
        "valore_catastale": f"{round(valore_catastale):,}".replace(",", "."),
        "imposta_registro": f"{round(imposta_registro):,}".replace(",", "."),
        "ristrutturazione": f"{round(ristrutturazione):,}".replace(",", "."),
        "totale_acquisto": f"{round(totale_acquisto):,}".replace(",", "."),
        "costi_vendita": f"{round(costi_vendita):,}".replace(",", "."),
        "valore_finale": f"{round(valore_finale):,}".replace(",", "."),
        "roi": f"{roi:.1f}%",
    }
    return results, form.to_dict()

@app.route("/", methods=["GET","POST"])
def index():
    formvals = {
        "ask":"150000","ipotecaria":"50","catastale":"50","agenzia":"3000","architetto":"2000",
        "condono":"0","condominio":"0","utenze":"500","imprevisti":"2000",
        "ristrut_tipo":"nessuna","ristrutturazione":"0",
        "tipo":"prima","rendita":"500","coeff":"115.5","imposta_pct":"2","imposta_registro":"0",
        "hs_percent":"2","ape":"200","dico":"250","provv_sale_pct":"3","vendita_imprevisti":"500",
        "street_price":"220000","inc_hs_pct":"5","inc_ristr_pct":"10"
    }
    active_tab = "acquisto"; results=None
    if request.method=="POST":
        active_tab=request.form.get("active_tab","acquisto")
        for k in formvals.keys():
            if k in request.form and request.form.get(k)!="":
                formvals[k]=request.form.get(k)
        results, formvals = compute_results(request.form)
    return render_template_string(HTML, results=results, active_tab=active_tab, formvals=formvals)

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)

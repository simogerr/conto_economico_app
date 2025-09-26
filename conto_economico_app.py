from flask import Flask, render_template_string, request, send_file
import io
import pandas as pd

app = Flask(__name__)

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
  .wrap{max-width:1000px;margin:0 auto;padding:20px}
  .card{background:rgba(17,24,39,.85);border:1px solid #1f2937;border-radius:14px;
        padding:16px;box-shadow:0 6px 20px rgba(0,0,0,.25);margin-bottom:16px}

  .tabs{display:flex;justify-content:center;gap:30px;margin-bottom:16px;border-bottom:2px solid #1f2937}
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

  .results{margin-top:20px}
  .pill{background:#0b1222;border:1px solid #1f2937;border-radius:12px;padding:10px;margin:6px 0}
  .grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}

  .preview{margin-top:10px;padding:12px;border-radius:12px;background:#0b1222;border:1px solid #1f2937}
  .preview h4{margin:0 0 8px;font-size:14px;color:#cbd5e1}
  .preview .item{display:flex;justify-content:space-between;margin:4px 0;font-size:14px}
  .preview .item span:first-child{color:#a7b2c3}
  .muted{color:#94a3b8;font-size:12px;margin-top:4px}
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
      <button type="button" class="tablink" data-tab="acquisto" onclick="openTab(event, 'acquisto')">Acquisto</button>
      <button type="button" class="tablink" data-tab="catastale" onclick="openTab(event, 'catastale')">Valore Catastale & Registro</button>
    </div>

    <!-- TAB ACQUISTO -->
    <div id="acquisto" class="tabcontent">
      <div class="row"><label>Acquisto immobile</label><input type="text" name="ask" value="{{ formvals.ask }}"></div>
      <div class="row"><label>Imposta ipotecaria</label><input type="text" name="ipotecaria" value="{{ formvals.ipotecaria }}"></div>
      <div class="row"><label>Imposta catastale</label><input type="text" name="catastale" value="{{ formvals.catastale }}"></div>
      <div class="row"><label>Imposta di registro</label><input type="text" value="{{ formvals.imposta_registro }}" readonly></div>
      <div class="row"><label>Provvigioni agenzia</label><input type="text" name="agenzia" value="{{ formvals.agenzia }}"></div>
      <div class="row"><label>Studio architetto</label><input type="text" name="architetto" value="{{ formvals.architetto }}"></div>
      <div class="row"><label>Condono</label><input type="text" name="condono" value="{{ formvals.condono }}"></div>
      <div class="row"><label>Spese condominiali insolute</label><input type="text" name="condominio" value="{{ formvals.condominio }}"></div>
      <div class="row"><label>Nuove utenze (luce+gas)</label><input type="text" name="utenze" value="{{ formvals.utenze }}"></div>
      <div class="row"><label>Imprevisti</label><input type="text" name="imprevisti" value="{{ formvals.imprevisti }}"></div>
      <!-- Nuova tendina ristrutturazione -->
      <div class="row">
        <label>Tipo di ristrutturazione</label>
        <select name="ristrut_tipo">
          <option value="nessuna" {% if formvals.ristrut_tipo=='nessuna' %}selected{% endif %}>Nessuna</option>
          <option value="piccola" {% if formvals.ristrut_tipo=='piccola' %}selected{% endif %}>Piccoli interventi (10%)</option>
          <option value="intermedia" {% if formvals.ristrut_tipo=='intermedia' %}selected{% endif %}>Ristrutturazione intermedia (20%)</option>
          <option value="complessa" {% if formvals.ristrut_tipo=='complessa' %}selected{% endif %}>Ristrutturazione complessa (60%)</option>
        </select>
      </div>
      <div class="row"><label>Costo ristrutturazione (calcolato)</label><input type="text" value="{{ formvals.ristrutturazione }}" readonly></div>

      <div class="actions"><button class="btn primary" type="submit">Calcola</button></div>
    </div>

    <!-- TAB CATASTALE -->
    <div id="catastale" class="tabcontent">
      <div class="row">
        <label>Tipo di proprietà</label>
        <select name="tipo" id="tipo" onchange="autoFillByTipo();updatePreview();">
          <option value="prima" {{ 'selected' if formvals.tipo=='prima' else '' }}>Prima casa</option>
          <option value="seconda" {{ 'selected' if formvals.tipo=='seconda' else '' }}>Seconda casa</option>
        </select>
      </div>
      <div class="row"><label>Rendita catastale</label><input type="text" id="rendita" name="rendita" value="{{ formvals.rendita }}" oninput="updatePreview()"></div>
      <div class="row"><label>Coefficiente</label><input type="text" id="coeff" name="coeff" value="{{ formvals.coeff }}" oninput="updatePreview()"></div>
      <div class="row"><label>Imposta di registro %</label><input type="text" id="imposta_pct" name="imposta_pct" value="{{ formvals.imposta_pct }}" oninput="updatePreview()"></div>
      <div class="preview">
        <h4>Anteprima calcoli</h4>
        <div class="item"><span>Valore catastale</span><span id="pv_val_cat">—</span></div>
        <div class="item"><span>Imposta di registro</span><span id="pv_imp_reg">—</span></div>
      </div>
      <div class="actions"><button class="btn primary" type="submit">Calcola</button></div>
    </div>
  </form>
</div>

{% if results %}
<div class="wrap card results">
  <h2>Riepilogo</h2>
  <div class="grid2">
    <div class="pill"><b>Tipo proprietà:</b> {{ results.tipo_label }}</div>
    <div class="pill"><b>Valore catastale:</b> {{ results.valore_catastale }}</div>
    <div class="pill"><b>Imposta di registro:</b> {{ results.imposta_registro }}</div>
    <div class="pill"><b>Costo ristrutturazione:</b> {{ results.ristrutturazione }}</div>
    <div class="pill"><b>Totale costi acquisto:</b> {{ results.totale }}</div>
  </div>
  <form method="post" action="/download" style="margin-top:12px">
    {% for k,v in formvals.items() %}
      <input type="hidden" name="{{k}}" value="{{v}}">
    {% endfor %}
    <button class="btn secondary" type="submit">Scarica Excel</button>
  </form>
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
function autoFillByTipo(){ let tipo=document.getElementById('tipo').value;
  if(tipo==='prima'){document.getElementById('coeff').value="115.5";document.getElementById('imposta_pct').value="2";}
  else{document.getElementById('coeff').value="126";document.getElementById('imposta_pct').value="9";} updatePreview();}
function updatePreview(){ let r=num(document.getElementById('rendita').value);
  let c=num(document.getElementById('coeff').value); let p=num(document.getElementById('imposta_pct').value);
  let val=r*c; let imp=val*(p/100); document.getElementById('pv_val_cat').innerHTML=fmt(val);
  document.getElementById('pv_imp_reg').innerHTML=fmt(imp); }
document.addEventListener('DOMContentLoaded',()=>{ openTab(null,"{{ active_tab or 'acquisto' }}"); updatePreview(); });
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

    tipo = form.get("tipo","prima")
    rendita = parse_num(form.get("rendita"))
    coeff = parse_num(form.get("coeff"))
    imposta_pct = parse_num(form.get("imposta_pct"))

    valore_catastale = rendita * coeff
    imposta_registro = valore_catastale * (imposta_pct / 100.0)

    # Calcolo ristrutturazione
    ristrut_tipo = form.get("ristrut_tipo","nessuna")
    perc = {"nessuna":0,"piccola":0.10,"intermedia":0.20,"complessa":0.60}[ristrut_tipo]
    ristrutturazione = ask * perc

    totale = (ask + ipotecaria + catastale_cost + agenzia + architetto +
              condono + condominio + utenze + imprevisti + ristrutturazione +
              imposta_registro)

    results = {
        "tipo_label": "Prima casa" if tipo=="prima" else "Seconda casa",
        "valore_catastale": f"{round(valore_catastale):,}".replace(",", "."),
        "imposta_registro": f"{round(imposta_registro):,}".replace(",", "."),
        "ristrutturazione": f"{round(ristrutturazione):,}".replace(",", "."),
        "totale": f"{round(totale):,}".replace(",", "."),
    }

    inputs = form.to_dict()
    inputs["imposta_registro"] = round(imposta_registro,2)
    inputs["ristrutturazione"] = round(ristrutturazione,2)
    return results, inputs

@app.route("/", methods=["GET","POST"])
def index():
    formvals = {"ask":"150000","ipotecaria":"50","catastale":"50","agenzia":"3000","architetto":"2000",
                "condono":"0","condominio":"0","utenze":"500","imprevisti":"2000",
                "tipo":"prima","rendita":"500","coeff":"115.5","imposta_pct":"2","imposta_registro":"0",
                "ristrut_tipo":"nessuna","ristrutturazione":"0"}
    active_tab = "acquisto"; results=None

    if request.method=="POST":
        active_tab=request.form.get("active_tab","acquisto")
        for k in formvals.keys():
            if k in request.form and request.form.get(k)!="": formvals[k]=request.form.get(k)
        results, formvals = compute_results(request.form)

    return render_template_string(HTML, results=results, active_tab=active_tab, formvals=formvals)

@app.route("/download", methods=["POST"])
def download_excel():
    results, inputs = compute_results(request.form)
    df_inputs = pd.DataFrame(inputs.items(), columns=["Voce","Valore"])
    df_results = pd.DataFrame(results.items(), columns=["Risultato","Valore"])
    output=io.BytesIO()
    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        df_inputs.to_excel(writer,index=False,sheet_name="Input")
        df_results.to_excel(writer,index=False,sheet_name="Risultati")
    output.seek(0)
    return send_file(output,as_attachment=True,download_name="deal_checker.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)

# conto_economico_app.py
from flask import Flask, render_template_string, request, send_file, redirect, url_for
import io
import pandas as pd
from openpyxl.utils import get_column_letter

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

# -------------------- calcoli compravendita --------------------
def compute_compravendita(form):
    titolo = form.get("titolo", "")
    ask = parse_num(form.get("ask"))
    ipotecaria = parse_num(form.get("ipotecaria"))
    catastale = parse_num(form.get("catastale"))
    agenzia = parse_num(form.get("agenzia"))
    architetto = parse_num(form.get("architetto"))
    condono = parse_num(form.get("condono"))
    condominio = parse_num(form.get("condominio"))
    utenze = parse_num(form.get("utenze"))
    imprevisti = parse_num(form.get("imprevisti"))

    ristrut_tipo = form.get("ristrut_tipo","nessuna")
    perc_map = {"nessuna":0,"piccola":0.10,"intermedia":0.20,"complessa":0.60}
    perc = perc_map.get(ristrut_tipo,0)
    ristrutturazione = ask * perc

    tipo_prop = form.get("tipo_prop","prima")
    rendita = parse_num(form.get("rendita"))
    coeff = 160 if tipo_prop=="prima" else 126
    imp_perc = 2 if tipo_prop=="prima" else 9
    valore_catastale = rendita * coeff
    imposta_registro = valore_catastale * (imp_perc/100)

    totale_acquisto = ask + ipotecaria + catastale + agenzia + architetto + condono + condominio + utenze + imprevisti + ristrutturazione + imposta_registro

    home_staging = parse_num(form.get("home_staging"))
    ape = parse_num(form.get("ape"))
    conformita = parse_num(form.get("conformita"))
    agenzia_v = parse_num(form.get("agenzia_v"))
    imprevisti_v = parse_num(form.get("imprevisti_v"))
    costi_vendita = home_staging + ape + conformita + agenzia_v + imprevisti_v

    street_price = parse_num(form.get("street_price"))
    inc_hs = parse_num(form.get("inc_hs"))
    inc_ristrut = parse_num(form.get("inc_ristrut"))
    valore_finale = street_price * (1+inc_hs/100) * (1+inc_ristrut/100)

    roi = ((valore_finale - totale_acquisto - costi_vendita) / totale_acquisto * 100) if totale_acquisto>0 else 0
    roi_class = "pill roi-good" if roi>30 else "pill"

    return {
        "titolo": titolo,
        "tipo_label": "Prima casa" if tipo_prop=="prima" else "Seconda casa",
        "valore_catastale": round(valore_catastale,2),
        "imposta_registro": round(imposta_registro,2),
        "ristrutturazione": round(ristrutturazione,2),
        "totale_acquisto": round(totale_acquisto,2),
        "costi_vendita": round(costi_vendita,2),
        "valore_finale": round(valore_finale,2),
        "roi": f"{roi:.1f}%",
        "roi_class": roi_class
    }

# -------------------- calcoli affitti --------------------
def compute_affitti(form):
    canone_mensile = parse_num(form.get("canone_mensile"))
    spese_mensili = parse_num(form.get("spese_mensili"))
    investimento_tot = parse_num(form.get("investimento_tot"))
    equity = parse_num(form.get("equity"))
    rata_mutuo = parse_num(form.get("rata_mutuo"))

    ricavi_annui = canone_mensile*12
    spese_annue = spese_mensili*12
    reddito_op = ricavi_annui - spese_annue
    cashflow = reddito_op - (rata_mutuo*12)

    roi = (reddito_op / investimento_tot *100) if investimento_tot>0 else 0
    roe = (cashflow / equity *100) if equity>0 else 0
    payback_mesi = (investimento_tot / (reddito_op/12)) if reddito_op>0 else 0

    proiezione=[]
    cumul_op=0;cumul_cash=0
    for anno in range(1,6):
        reddito_op_y = reddito_op
        cashflow_y = cashflow
        cumul_op += reddito_op_y
        cumul_cash += cashflow_y
        roi_cum = (cumul_op/investimento_tot*100) if investimento_tot>0 else 0
        roe_cum = (cumul_cash/equity*100) if equity>0 else 0
        proiezione.append({
            "Anno": anno,
            "Reddito operativo": f"{round(reddito_op_y):,}".replace(",","."),
            "Cashflow": f"{round(cashflow_y):,}".replace(",","."),
            "ROI cumulato": f"{roi_cum:.1f}%",
            "ROE cumulato": f"{roe_cum:.1f}%"
        })
    return {
        "ricavi_annui": round(ricavi_annui,2),
        "spese_annue": round(spese_annue,2),
        "reddito_op": round(reddito_op,2),
        "cashflow": round(cashflow,2),
        "roi": round(roi,2),
        "roe": round(roe,2),
        "payback_mesi": round(payback_mesi,1),
        "proiezione": proiezione
    }

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
  .card.results{background:#1e293b;}

  .parent-tabs{display:flex;justify-content:center;margin:14px auto 0;flex-wrap:wrap}
  .segment{display:flex;gap:0;background:#0b1222;border:1px solid #1f2937;border-radius:12px;
    padding:4px;box-shadow:inset 0 0 0 1px #0b1222}
  .parent-btn{background:transparent;border:none;color:#94a3b8;font-weight:700;font-size:14px;
    padding:8px 14px;border-radius:8px;cursor:pointer;transition:all .2s}
  .parent-btn:hover{color:#e5e7eb}
  .parent-btn.active{background:#17243a;color:#e5e7eb;box-shadow:0 0 0 1px #243b55 inset}

  .row{margin:8px 0;display:flex;gap:10px;align-items:center}
  .row label{flex:1}
  .row input, .row select{flex:1;padding:10px;border-radius:10px;border:1px solid var(--ring);background:#0b1023;color:var(--txt)}

  .actions{display:flex;gap:10px;justify-content:flex-end;margin-top:12px}
  .btn{padding:8px 14px;border:none;border-radius:10px;cursor:pointer;font-weight:700}
  .primary{background:linear-gradient(180deg,#16a34a,#15803d);color:#fff}
  .secondary{background:#0b1222;color:#e5e7eb;border:1px solid #1f2937}

  .pill{background:#0b1222;border:1px solid #1f2937;border-radius:12px;padding:10px;margin:6px 0}
  .pill.roi-good { background:#14532d; border:1px solid #15803d; color:#d1fae5; }

  table{width:100%;border-collapse:collapse;margin-top:12px}
  th,td{padding:8px;border-bottom:1px solid #1f2937;text-align:center}
  th{background:#17243a}
</style>
</head>
<body>
<header>
  <h1>Calcolo Conto Economico</h1>
  <p>Strumento per analisi investimenti immobiliari</p>
</header>

<div class="wrap card">
  <div class="parent-tabs">
    <div class="segment">
      <button type="button" class="parent-btn" data-parent="compravendita" onclick="openParent('compravendita')">Compravendita</button>
      <button type="button" class="parent-btn" data-parent="affitti" onclick="openParent('affitti')">Affitti</button>
    </div>
  </div>
</div>

<!-- ========================== COMPRAVENDITA ========================== -->
<div class="wrap card parent-section" id="parent-compravendita">
  <form method="post">
    <input type="hidden" id="parent_tab" name="parent_tab" value="{{ parent_tab or 'compravendita' }}"/>

    <div class="row"><label>Titolo operazione</label><input type="text" name="titolo" value="{{ formvals.titolo }}"></div>
    <div class="row"><label>Prezzo acquisto immobile</label><input type="text" name="ask" value="{{ formvals.ask }}"></div>
    <div class="row"><label>Imposta ipotecaria</label><input type="text" name="ipotecaria" value="{{ formvals.ipotecaria }}"></div>
    <div class="row"><label>Imposta catastale</label><input type="text" name="catastale" value="{{ formvals.catastale }}"></div>
    <div class="row"><label>Provvigioni agenzia</label><input type="text" name="agenzia" value="{{ formvals.agenzia }}"></div>
    <div class="row"><label>Studio architetto</label><input type="text" name="architetto" value="{{ formvals.architetto }}"></div>
    <div class="row"><label>Condono</label><input type="text" name="condono" value="{{ formvals.condono }}"></div>
    <div class="row"><label>Spese condominiali insolute</label><input type="text" name="condominio" value="{{ formvals.condominio }}"></div>
    <div class="row"><label>Nuove utenze</label><input type="text" name="utenze" value="{{ formvals.utenze }}"></div>
    <div class="row"><label>Imprevisti</label><input type="text" name="imprevisti" value="{{ formvals.imprevisti }}"></div>
    <div class="row">
      <label>Tipo di ristrutturazione</label>
      <select name="ristrut_tipo">
        <option value="nessuna" {% if formvals.ristrut_tipo=='nessuna' %}selected{% endif %}>Nessuna</option>
        <option value="piccola" {% if formvals.ristrut_tipo=='piccola' %}selected{% endif %}>Piccoli interventi (10%)</option>
        <option value="intermedia" {% if formvals.ristrut_tipo=='intermedia' %}selected{% endif %}>Ristrutturazione intermedia (20%)</option>
        <option value="complessa" {% if formvals.ristrut_tipo=='complessa' %}selected{% endif %}>Ristrutturazione complessa (60%)</option>
      </select>
    </div>
    <div class="row"><label>Rendita catastale</label><input type="text" name="rendita" value="{{ formvals.rendita }}"></div>
    <div class="row">
      <label>Tipo proprietà</label>
      <select name="tipo_prop">
        <option value="prima" {% if formvals.tipo_prop=='prima' %}selected{% endif %}>Prima casa</option>
        <option value="seconda" {% if formvals.tipo_prop=='seconda' %}selected{% endif %}>Seconda casa</option>
      </select>
    </div>

    <h3>Costi messa in vendita</h3>
    <div class="row"><label>Home staging</label><input type="text" name="home_staging" value="{{ formvals.home_staging }}"></div>
    <div class="row"><label>APE</label><input type="text" name="ape" value="{{ formvals.ape }}"></div>
    <div class="row"><label>Conformità impianti</label><input type="text" name="conformita" value="{{ formvals.conformita }}"></div>
    <div class="row"><label>Provvigione agenzia (vendita)</label><input type="text" name="agenzia_v" value="{{ formvals.agenzia_v }}"></div>
    <div class="row"><label>Imprevisti</label><input type="text" name="imprevisti_v" value="{{ formvals.imprevisti_v }}"></div>

    <h3>Nuovo Valore</h3>
    <div class="row"><label>Street price</label><input type="text" name="street_price" value="{{ formvals.street_price }}"></div>
    <div class="row"><label>Incremento % home staging</label><input type="text" name="inc_hs" value="{{ formvals.inc_hs }}"></div>
    <div class="row"><label>Incremento % ristrutturazione</label><input type="text" name="inc_ristrut" value="{{ formvals.inc_ristrut }}"></div>

    <div class="actions">
      <button class="btn primary" type="submit">Calcola</button>
      <a href="{{ url_for('reset') }}" class="btn secondary">Reset</a>
    </div>
  </form>
</div>

{% if results %}
<div class="wrap card results">
  <h2>Riepilogo Compravendita</h2>
  <div class="pill"><b>Titolo:</b> {{ results.titolo }}</div>
  <div class="pill"><b>Tipo proprietà:</b> {{ results.tipo_label }}</div>
  <div class="pill"><b>Valore catastale:</b> {{ results.valore_catastale }}</div>
  <div class="pill"><b>Imposta di registro:</b> {{ results.imposta_registro }}</div>
  <div class="pill"><b>Costo ristrutturazione:</b> {{ results.ristrutturazione }}</div>
  <div class="pill"><b>Totale costi acquisto:</b> {{ results.totale_acquisto }}</div>
  <div class="pill"><b>Costi messa in vendita:</b> {{ results.costi_vendita }}</div>
  <div class="{{ results.roi_class }}"><b>ROI:</b> {{ results.roi }}</div>
  <div class="pill"><b>Valore finale percepito:</b> {{ results.valore_finale }}</div>
  <div class="actions">
    <a href="{{ url_for('download') }}" class="btn primary">⬇️ Scarica Excel</a>
  </div>
</div>
{% endif %}

<!-- ========================== AFFITTI ========================== -->
<div class="wrap card parent-section" id="parent-affitti" style="display:none">
  <form method="post">
    <input type="hidden" id="parent_tab" name="parent_tab" value="{{ parent_tab or 'affitti' }}"/>
    <div class="row"><label>Canone mensile</label><input type="text" name="canone_mensile" value="{{ formvals.canone_mensile }}"></div>
    <div class="row"><label>Spese mensili</label><input type="text" name="spese_mensili" value="{{ formvals.spese_mensili }}"></div>
    <div class="row"><label>Investimento totale</label><input type="text" name="investimento_tot" value="{{ formvals.investimento_tot }}"></div>
    <div class="row"><label>Equity (capitale proprio)</label><input type="text" name="equity" value="{{ formvals.equity }}"></div>
    <div class="row"><label>Rata mutuo mensile</label><input type="text" name="rata_mutuo" value="{{ formvals.rata_mutuo }}"></div>
    <div class="actions">
      <button class="btn primary" type="submit">Calcola</button>
      <a href="{{ url_for('reset') }}" class="btn secondary">Reset</a>
    </div>
  </form>
</div>

{% if results_af %}
<div class="wrap card results">
  <h2>Riepilogo Affitti</h2>
  <div class="pill"><b>Ricavi annui:</b> {{ results_af.ricavi_annui }}</div>
  <div class="pill"><b>Spese annue:</b> {{ results_af.spese_annue }}</div>
  <div class="pill"><b>Reddito operativo:</b> {{ results_af.reddito_op }}</div>
  <div class="pill"><b>Cashflow annuo:</b> {{ results_af.cashflow }}</div>
  <div class="pill"><b>ROI:</b> {{ results_af.roi }}%</div>
  <div class="pill"><b>ROE:</b> {{ results_af.roe }}%</div>
  <div class="pill"><b>Rientro investimento:</b> {{ results_af.payback_mesi }} mesi</div>
  <h3>Proiezione 5 anni</h3>
  <table>
    <tr><th>Anno</th><th>Reddito operativo</th><th>Cashflow</th><th>ROI cumulato</th><th>ROE cumulato</th></tr>
    {% for row in results_af.proiezione %}
      <tr><td>{{ row.Anno }}</td><td>{{ row['Reddito operativo'] }}</td><td>{{ row.Cashflow }}</td><td>{{ row['ROI cumulato'] }}</td><td>{{ row['ROE cumulato'] }}</td></tr>
    {% endfor %}
  </table>
  <div class="actions">
    <a href="{{ url_for('download_af') }}" class="btn primary">⬇️ Scarica Excel</a>
  </div>
</div>
{% endif %}

<script>
function openParent(tab){
  document.querySelectorAll(".parent-section").forEach(s=>s.style.display="none");
  document.querySelector("#parent-"+tab).style.display="block";
  document.querySelectorAll(".parent-btn").forEach(b=>b.classList.remove("active"));
  document.querySelector(".parent-btn[data-parent='"+tab+"']").classList.add("active");
  document.getElementById("parent_tab").value=tab;
}
openParent("{{ parent_tab or 'compravendita' }}");
</script>
</body>
</html>
"""

# -------------------- routes --------------------
@app.route("/", methods=["GET","POST"])
def index():
    parent_tab = request.form.get("parent_tab","compravendita")
    formvals = {k:request.form.get(k,"") for k in request.form}
    results=None;results_af=None
    if request.method=="POST":
        if parent_tab=="compravendita":
            results=compute_compravendita(request.form)
        elif parent_tab=="affitti":
            results_af=compute_affitti(request.form)
    return render_template_string(HTML, formvals=formvals, results=results, results_af=results_af, parent_tab=parent_tab)

@app.route("/download")
def download():
    results = compute_compravendita(request.args)
    df = pd.DataFrame(results.items(), columns=["Voce","Valore"])
    output=io.BytesIO()
    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        df.to_excel(writer,index=False)
        for sheet in writer.sheets.values():
            for col in sheet.columns:
                length=max(len(str(c.value)) if c.value else 0 for c in col)
                sheet.column_dimensions[get_column_letter(col[0].column)].width=length+2
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="compravendita.xlsx")

@app.route("/download_af")
def download_af():
    results = compute_affitti(request.args)
    df1 = pd.DataFrame([
        ["Ricavi annui",results["ricavi_annui"]],
        ["Spese annue",results["spese_annue"]],
        ["Reddito operativo",results["reddito_op"]],
        ["Cashflow",results["cashflow"]],
        ["ROI (%)",results["roi"]],
        ["ROE (%)",results["roe"]],
        ["Rientro investimento (mesi)",results["payback_mesi"]],
    ],columns=["Voce","Valore"])
    df2 = pd.DataFrame(results["proiezione"])
    output=io.BytesIO()
    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        df1.to_excel(writer,sheet_name="Riepilogo",index=False)
        df2.to_excel(writer,sheet_name="Proiezione_5_anni",index=False)
        for sheet in writer.sheets.values():
            for col in sheet.columns:
                length=max(len(str(c.value)) if c.value else 0 for c in col)
                sheet.column_dimensions[get_column_letter(col[0].column)].width=length+2
    output.seek(0)
    return send_file(output,as_attachment=True,download_name="affitti.xlsx")

@app.route("/reset")
def reset(): return redirect(url_for("index"))

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)

#!/usr/bin/env python3
"""
Suivi Épargne — version web pour Termux / navigateur.
Lance : python savings/web_app.py
Ouvre : http://localhost:8080
Dépendances : aucune (stdlib uniquement)
"""

import sqlite3
import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

GOAL = 1_000_000.0

MONTH_NAMES_FR = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]

VEHICLE_COLORS = [
    "#1976D2", "#7B1FA2", "#E64A19",
    "#388E3C", "#F57C00", "#0097A7", "#C62828",
]

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savings.db")


# ── Base de données ───────────────────────────────────────────────────────────

def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS vehicles (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT    NOT NULL UNIQUE,
            monthly_amount REAL    NOT NULL DEFAULT 0,
            current_total  REAL    NOT NULL DEFAULT 0,
            color_idx      INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS entries (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER REFERENCES vehicles(id) ON DELETE CASCADE,
            year       INTEGER NOT NULL,
            month      INTEGER NOT NULL,
            amount     REAL    NOT NULL,
            note       TEXT,
            created_at TEXT    DEFAULT (datetime('now'))
        );
    """)
    if not conn.execute("SELECT 1 FROM vehicles LIMIT 1").fetchone():
        conn.executemany(
            "INSERT OR IGNORE INTO vehicles (name, monthly_amount, current_total, color_idx)"
            " VALUES (?,?,?,?)",
            [
                ("Assurance Vie", 743.63, 0.0, 0),
                ("PER",            30.0,  0.0, 1),
                ("PEL",            50.0,  0.0, 2),
            ],
        )
        conn.commit()
    return conn


def fmt_money(amount):
    parts = f"{abs(amount):,.2f}".split(".")
    sign = "-" if amount < 0 else ""
    return f"{sign}{parts[0].replace(',', ' ')},{parts[1]} €"


def get_stats(conn):
    rows    = conn.execute("SELECT * FROM vehicles ORDER BY id").fetchall()
    total   = sum(r["current_total"]  for r in rows)
    monthly = sum(r["monthly_amount"] for r in rows)
    pct     = min(total / GOAL * 100, 100) if GOAL else 0
    if total >= GOAL:
        months_left = 0
    elif monthly > 0:
        months_left = (GOAL - total) / monthly
    else:
        months_left = float("inf")
    return [dict(r) for r in rows], total, monthly, pct, months_left


# ── HTML ─────────────────────────────────────────────────────────────────────

HTML_STYLE = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, sans-serif; background: #0d1117; color: #c9d1d9; }
  .header { background: #0a1628; padding: 16px; text-align: center; }
  .header h1 { color: #ffd700; font-size: 22px; }
  .header .sub { color: #aaa; font-size: 13px; margin-top: 4px; }
  .progress-wrap { background: #1a1a2e; border-radius: 8px; height: 18px; margin: 10px 0; overflow: hidden; }
  .progress-bar  { height: 100%; background: linear-gradient(90deg, #1976D2, #7B1FA2); transition: width .4s; }
  .card { background: #161b22; border-radius: 8px; padding: 14px; margin: 10px; }
  .card h2 { font-size: 16px; color: #58a6ff; margin-bottom: 10px; }
  .vehicle { border-left: 4px solid; padding: 10px; margin: 8px 0; border-radius: 4px; background: #0d1117; }
  .amount  { font-size: 20px; font-weight: bold; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th  { background: #1a1a2e; padding: 8px; text-align: left; }
  td  { padding: 8px; border-bottom: 1px solid #21262d; }
  form input, form select { width: 100%; padding: 8px; margin: 4px 0 10px; border-radius: 4px;
    border: 1px solid #30363d; background: #0d1117; color: #c9d1d9; font-size: 14px; }
  .btn  { display: inline-block; padding: 10px 20px; border-radius: 6px; border: none;
    cursor: pointer; font-size: 14px; color: #fff; text-decoration: none; }
  .btn-primary { background: #238636; }
  .btn-danger  { background: #da3633; font-size: 12px; padding: 5px 10px; }
  .btn-info    { background: #1f6feb; }
  nav { display: flex; gap: 8px; padding: 10px; background: #0a1628; }
  nav a { color: #58a6ff; text-decoration: none; padding: 6px 12px; border-radius: 4px;
    background: #1a2a40; font-size: 13px; }
  nav a.active { background: #1f6feb; color: #fff; }
  .green { color: #56d364; }
  .orange { color: #f0883e; }
  .red { color: #f85149; }
  .small { font-size: 11px; color: #8b949e; }
  .eta { background: #0f2d45; border-radius: 6px; padding: 10px; margin: 8px 0;
    text-align: center; font-size: 13px; color: #79c0ff; }
  .proj-row { display: flex; justify-content: space-between; padding: 8px 0;
    border-bottom: 1px solid #21262d; }
</style>
"""


def page(title, nav_active, body, msg=""):
    msg_html = f'<div style="background:#238636;padding:10px;margin:10px;border-radius:6px;">{msg}</div>' if msg else ""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
{HTML_STYLE}
</head>
<body>
<div class="header">
  <h1>💰 Objectif Épargne — 1 000 000 €</h1>
  <div class="sub" id="hdr-sub">Chargement…</div>
  <div class="progress-wrap"><div class="progress-bar" id="pbar" style="width:0%"></div></div>
</div>
<nav>
  <a href="/" {"class='active'" if nav_active=='dashboard' else ''}>📊 Bilan</a>
  <a href="/comptes" {"class='active'" if nav_active=='comptes' else ''}>🏦 Comptes</a>
  <a href="/saisir" {"class='active'" if nav_active=='saisir' else ''}>➕ Saisir</a>
  <a href="/historique" {"class='active'" if nav_active=='historique' else ''}>📋 Historique</a>
</nav>
{msg_html}
{body}
<script>
fetch('/api/stats').then(r=>r.json()).then(d=>{{
  document.getElementById('hdr-sub').textContent =
    d.total_fmt + ' / ' + d.goal_fmt + '  •  ' + d.pct.toFixed(2) + '%  •  ' + d.monthly_fmt + '/mois';
  document.getElementById('pbar').style.width = d.pct + '%';
}});
</script>
</body></html>"""


def render_dashboard(conn):
    rows, total, monthly, pct, months_left = get_stats(conn)
    reste = max(GOAL - total, 0)

    vehicles_html = ""
    for row in rows:
        color = VEHICLE_COLORS[row["color_idx"] % len(VEHICLE_COLORS)]
        pct_v = row["current_total"] / GOAL * 100
        name_h = row["name"]
        total_h = fmt_money(row["current_total"])
        monthly_h = fmt_money(row["monthly_amount"])
        vehicles_html += f"""
        <div class="vehicle" style="border-color:{color}">
          <div style="color:{color};font-weight:bold;font-size:15px">{name_h}</div>
          <div class="amount" style="color:{color}">{total_h}</div>
          <div class="small">{pct_v:.3f}% de l'objectif &nbsp;|&nbsp; {monthly_h} / mois</div>
        </div>"""

    rate_options = "".join(
        f'<option value="{p}" {"selected" if p == 3 else ""}>{p} %</option>'
        for p in range(1, 31)
    )

    body = f"""
<div class="card">
  <div style="font-size:28px;font-weight:bold;color:#ffd700;text-align:center">{fmt_money(total)}</div>
  <div style="text-align:center;color:#aaa;margin:6px 0">sur {fmt_money(GOAL)} — {pct:.2f}%</div>
  <div class="progress-wrap"><div class="progress-bar" style="width:{pct}%"></div></div>
  <div style="text-align:center;color:#aaa;font-size:13px">Reste : <span class="orange">{fmt_money(reste)}</span></div>
  <div class="eta" id="eta">…</div>
</div>
<div class="card">
  <h2>💳 Versements mensuels</h2>
  <div style="font-size:22px;color:#56d364;font-weight:bold">{fmt_money(monthly)} / mois</div>
</div>
<div class="card">
  <h2>🏦 Répartition par compte</h2>
  {vehicles_html}
</div>
<div class="card">
  <h2>📈 Projections (intérêts composés)</h2>
  <label class="small">Rendement annuel</label>
  <select id="rate" onchange="recompute()">{rate_options}</select>
  <div id="proj"></div>
</div>
<script>
  var TOTAL={total}, MONTHLY={monthly}, GOAL={GOAL};
  function fmtMoney(a){{
    var sign = a<0 ? '-' : '';
    a = Math.abs(a).toFixed(2).split('.');
    return sign + a[0].replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,' ') + ',' + a[1] + ' €';
  }}
  function futureValue(p, pmt, ratePct, months){{
    if(ratePct<=0) return p + pmt*months;
    var i = ratePct/100/12;
    var g = Math.pow(1+i, months);
    return p*g + pmt*((g-1)/i);
  }}
  function monthsToGoal(p, pmt, ratePct, goal){{
    if(p>=goal) return 0;
    if(ratePct<=0) return pmt>0 ? (goal-p)/pmt : Infinity;
    var i = ratePct/100/12;
    var base = p + pmt/i;
    if(base<=0) return Infinity;
    var target = (goal + pmt/i)/base;
    if(target<=1) return Infinity;
    return Math.log(target)/Math.log(1+i);
  }}
  function recompute(){{
    var rate = parseInt(document.getElementById('rate').value);
    // ETA
    var m = monthsToGoal(TOTAL, MONTHLY, rate, GOAL);
    var eta = document.getElementById('eta');
    if(TOTAL>=GOAL){{ eta.textContent = '🎉 Objectif atteint !'; }}
    else if(!isFinite(m)){{ eta.textContent = '⏱ Configurez vos versements mensuels'; }}
    else {{
      var yrs = m/12;
      eta.textContent = yrs>=2
        ? '⏱ ~'+yrs.toFixed(1)+' ans ('+Math.round(m)+' mois) à '+rate+'% de rendement'
        : '⏱ ~'+Math.round(m)+' mois à '+rate+'% de rendement';
    }}
    // Projections
    var rows = [['1 an',12],['5 ans',60],['10 ans',120],['20 ans',240]];
    var html = '';
    for(var k=0;k<rows.length;k++){{
      var months = rows[k][1];
      var fv = futureValue(TOTAL, MONTHLY, rate, months);
      var gains = fv - (TOTAL + MONTHLY*months);
      var color = fv>=GOAL ? '#56d364' : '#f0883e';
      var trophy = fv>=GOAL ? ' 🏆' : '';
      html += '<div class="proj-row"><span>Dans '+rows[k][0]
            + '<br><span style="color:#777;font-size:10px">dont +'+fmtMoney(gains)+' d\\'intérêts</span></span>'
            + '<span style="color:'+color+';font-weight:bold">'+fmtMoney(fv)+trophy+'</span></div>';
    }}
    document.getElementById('proj').innerHTML = html;
  }}
  recompute();
</script>"""
    return page("Bilan — Épargne 1M", "dashboard", body)


def render_comptes(conn, msg=""):
    rows, *_ = get_stats(conn)
    vehicles_html = ""
    for row in rows:
        color = VEHICLE_COLORS[row["color_idx"] % len(VEHICLE_COLORS)]
        vid       = row["id"]
        name_h    = row["name"]
        total_v   = row["current_total"]
        monthly_v = row["monthly_amount"]
        vehicles_html += f"""
        <div class="card" style="border-left:4px solid {color}">
          <h2 style="color:{color}">{name_h}</h2>
          <form method="POST" action="/comptes/update">
            <input type="hidden" name="id" value="{vid}">
            <label class="small">Total épargné (€)</label>
            <input type="number" name="total" value="{total_v:.2f}" step="0.01" min="0">
            <label class="small">Versement mensuel (€)</label>
            <input type="number" name="monthly" value="{monthly_v:.2f}" step="0.01" min="0">
            <button class="btn btn-primary" type="submit">💾 Sauvegarder</button>
          </form>
          <form method="POST" action="/comptes/delete" style="margin-top:8px"
                onsubmit="return confirm('Supprimer ce compte ?')">
            <input type="hidden" name="id" value="{vid}">
            <button class="btn btn-danger" type="submit">🗑 Supprimer</button>
          </form>
        </div>"""

    body = f"""
{vehicles_html}
<div class="card">
  <h2>➕ Ajouter un compte</h2>
  <form method="POST" action="/comptes/add">
    <label class="small">Nom du compte</label>
    <input type="text" name="name" placeholder="ex: Livret A" required>
    <label class="small">Versement mensuel (€)</label>
    <input type="number" name="monthly" value="0" step="0.01" min="0">
    <label class="small">Total déjà épargné (€)</label>
    <input type="number" name="total" value="0" step="0.01" min="0">
    <button class="btn btn-info" type="submit">➕ Ajouter</button>
  </form>
</div>"""
    return page("Comptes — Épargne 1M", "comptes", body, msg)


def render_saisir(conn, msg=""):
    rows, *_ = get_stats(conn)
    now = datetime.now()
    options_vehicles = "".join(f'<option value="{r["id"]}">{r["name"]}</option>' for r in rows)
    options_months   = "".join(
        f'<option value="{i}" {"selected" if i == now.month else ""}>{MONTH_NAMES_FR[i]}</option>'
        for i in range(1, 13)
    )
    body = f"""
<div class="card">
  <h2>➕ Enregistrer un versement</h2>
  <form method="POST" action="/saisir/add">
    <label class="small">Compte</label>
    <select name="vehicle_id">{options_vehicles}</select>
    <label class="small">Mois / Année</label>
    <div style="display:flex;gap:8px">
      <select name="month" style="flex:2">{options_months}</select>
      <input type="number" name="year" value="{now.year}" min="2000" max="2100" style="flex:1">
    </div>
    <label class="small">Montant versé (€)</label>
    <input type="number" name="amount" placeholder="ex: 743.63" step="0.01" min="0.01" required>
    <label class="small">Note (optionnel)</label>
    <input type="text" name="note" placeholder="ex: virement automatique">
    <button class="btn btn-primary" type="submit">💾 Enregistrer</button>
  </form>
</div>
<div style="text-align:center;color:#555;font-size:12px;padding:10px">
  💡 Chaque versement est ajouté au total du compte concerné.
</div>"""
    return page("Saisir — Épargne 1M", "saisir", body, msg)


def render_historique(conn):
    entries = conn.execute("""
        SELECT e.id, e.year, e.month, e.amount, e.note, e.created_at,
               v.name AS vname, v.color_idx
        FROM entries e
        JOIN vehicles v ON v.id = e.vehicle_id
        ORDER BY e.year DESC, e.month DESC, e.created_at DESC
        LIMIT 200
    """).fetchall()

    if not entries:
        rows_html = '<tr><td colspan="5" style="text-align:center;color:#555">Aucun versement — utilisez ➕ Saisir</td></tr>'
    else:
        rows_html = ""
        for e in entries:
            mn = MONTH_NAMES_FR[e["month"]] if 1 <= e["month"] <= 12 else str(e["month"])
            color = VEHICLE_COLORS[e["color_idx"] % len(VEHICLE_COLORS)]
            note = e["note"] or ""
            rows_html += f"""
            <tr>
              <td style="color:{color}">{e['vname']}</td>
              <td>{mn} {e['year']}</td>
              <td class="green" style="font-weight:bold">{fmt_money(e['amount'])}</td>
              <td class="small">{note}</td>
              <td>
                <form method="POST" action="/historique/delete"
                      onsubmit="return confirm('Supprimer ce versement ?')" style="margin:0">
                  <input type="hidden" name="id" value="{e['id']}">
                  <button class="btn btn-danger" type="submit">✕</button>
                </form>
              </td>
            </tr>"""

    body = f"""
<div class="card">
  <table>
    <thead><tr><th>Compte</th><th>Période</th><th>Montant</th><th>Note</th><th></th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>"""
    return page("Historique — Épargne 1M", "historique", body)


# ── Serveur HTTP ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # silencieux

    def send_html(self, html, code=200):
        data = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, obj):
        data = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, path):
        self.send_response(303)
        self.send_header("Location", path)
        self.end_headers()

    def read_form(self):
        length = int(self.headers.get("Content-Length", 0))
        raw    = self.rfile.read(length).decode("utf-8")
        params = {}
        for pair in raw.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                from urllib.parse import unquote_plus
                params[unquote_plus(k)] = unquote_plus(v)
        return params

    def do_GET(self):
        parsed = urlparse(self.path)
        conn   = db_connect()
        try:
            if parsed.path == "/":
                self.send_html(render_dashboard(conn))
            elif parsed.path == "/comptes":
                self.send_html(render_comptes(conn))
            elif parsed.path == "/saisir":
                self.send_html(render_saisir(conn))
            elif parsed.path == "/historique":
                self.send_html(render_historique(conn))
            elif parsed.path == "/api/stats":
                rows, total, monthly, pct, months_left = get_stats(conn)
                self.send_json({
                    "total": total, "total_fmt": fmt_money(total),
                    "monthly": monthly, "monthly_fmt": fmt_money(monthly),
                    "pct": pct, "goal_fmt": fmt_money(GOAL),
                })
            else:
                self.send_html("<h1>404</h1>", 404)
        finally:
            conn.close()

    def do_POST(self):
        conn   = db_connect()
        params = self.read_form()
        try:
            if self.path == "/comptes/update":
                vid     = int(params.get("id", 0))
                total   = float(params.get("total", 0))
                monthly = float(params.get("monthly", 0))
                conn.execute(
                    "UPDATE vehicles SET current_total=?, monthly_amount=? WHERE id=?",
                    (total, monthly, vid),
                )
                conn.commit()
                self.redirect("/comptes")

            elif self.path == "/comptes/delete":
                vid = int(params.get("id", 0))
                conn.execute("DELETE FROM vehicles WHERE id=?", (vid,))
                conn.commit()
                self.redirect("/comptes")

            elif self.path == "/comptes/add":
                name    = params.get("name", "").strip()
                monthly = float(params.get("monthly", 0))
                total   = float(params.get("total", 0))
                if name:
                    count = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
                    conn.execute(
                        "INSERT OR IGNORE INTO vehicles (name, monthly_amount, current_total, color_idx)"
                        " VALUES (?,?,?,?)",
                        (name, monthly, total, count % len(VEHICLE_COLORS)),
                    )
                    conn.commit()
                self.redirect("/comptes")

            elif self.path == "/saisir/add":
                vid    = int(params.get("vehicle_id", 0))
                year   = int(params.get("year", datetime.now().year))
                month  = int(params.get("month", datetime.now().month))
                amount = float(params.get("amount", 0))
                note   = params.get("note", "").strip() or None
                if amount > 0 and vid:
                    conn.execute(
                        "INSERT INTO entries (vehicle_id, year, month, amount, note) VALUES (?,?,?,?,?)",
                        (vid, year, month, amount, note),
                    )
                    conn.execute(
                        "UPDATE vehicles SET current_total = current_total + ? WHERE id=?",
                        (amount, vid),
                    )
                    conn.commit()
                self.redirect("/saisir")

            elif self.path == "/historique/delete":
                eid = int(params.get("id", 0))
                row = conn.execute("SELECT vehicle_id, amount FROM entries WHERE id=?", (eid,)).fetchone()
                if row:
                    conn.execute("DELETE FROM entries WHERE id=?", (eid,))
                    conn.execute(
                        "UPDATE vehicles SET current_total = MAX(0, current_total - ?) WHERE id=?",
                        (row["amount"], row["vehicle_id"]),
                    )
                    conn.commit()
                self.redirect("/historique")

            else:
                self.send_html("<h1>404</h1>", 404)
        finally:
            conn.close()


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"✅ Serveur démarré → http://localhost:{port}")
    print("   Ouvrez cette adresse dans votre navigateur.")
    print("   Ctrl+C pour arrêter.\n")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

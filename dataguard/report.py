#!/usr/bin/env python3
"""DataGuard — génération du rapport HTML."""

import html
from datetime import datetime

from detectors import Finding, SEVERITY_HIGH, SEVERITY_MEDIUM, sort_findings

_SEVERITY_COLOR = {
    SEVERITY_HIGH: "#e74c3c",
    SEVERITY_MEDIUM: "#e67e22",
    "faible": "#3498db",
}


def build_html(findings: list[Finding], target: str) -> str:
    """Construit un rapport HTML autonome à partir des fuites détectées."""
    findings = sort_findings(findings)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    high = sum(1 for f in findings if f.severity == SEVERITY_HIGH)
    medium = sum(1 for f in findings if f.severity == SEVERITY_MEDIUM)
    low = len(findings) - high - medium

    rows = []
    for f in findings:
        color = _SEVERITY_COLOR.get(f.severity, "#7f8c8d")
        rows.append(
            f"<tr>"
            f"<td><span class='badge' style='background:{color}'>{html.escape(f.severity)}</span></td>"
            f"<td>{html.escape(f.type)}</td>"
            f"<td class='mono'>{html.escape(f.file)}:{f.line}</td>"
            f"<td class='mono'>{html.escape(f.excerpt)}</td>"
            f"</tr>"
        )
    rows_html = "\n".join(rows) if rows else (
        "<tr><td colspan='4'>Aucune donnée sensible détectée. ✓</td></tr>"
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Rapport DataGuard</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #2c3e50; }}
  h1 {{ margin-bottom: 0; }}
  .meta {{ color: #7f8c8d; margin-bottom: 1.5rem; }}
  .summary {{ display: flex; gap: 1rem; margin-bottom: 1.5rem; }}
  .card {{ padding: 1rem 1.5rem; border-radius: 8px; color: #fff; font-weight: bold; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ text-align: left; padding: 0.6rem 0.8rem; border-bottom: 1px solid #ecf0f1; }}
  th {{ background: #34495e; color: #fff; }}
  .badge {{ color: #fff; padding: 0.15rem 0.6rem; border-radius: 12px; font-size: 0.8rem; }}
  .mono {{ font-family: ui-monospace, monospace; font-size: 0.85rem; }}
</style>
</head>
<body>
  <h1>🛡️ Rapport DataGuard</h1>
  <p class="meta">Cible : <strong>{html.escape(target)}</strong> — généré le {generated}</p>
  <div class="summary">
    <div class="card" style="background:#e74c3c">Élevée : {high}</div>
    <div class="card" style="background:#e67e22">Moyenne : {medium}</div>
    <div class="card" style="background:#3498db">Faible : {low}</div>
  </div>
  <table>
    <thead>
      <tr><th>Gravité</th><th>Type</th><th>Emplacement</th><th>Extrait masqué</th></tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</body>
</html>
"""

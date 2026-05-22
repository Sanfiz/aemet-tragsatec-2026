# --------------------
# inject_data_into_qmd.py
# Inyecta embalses_data_v2.json (con BSS/AUC) en el .qmd antiguo,
# reemplazando el EMBALSES_DATA inline. Mantiene HINDCAST_MAP y todo lo demás.
# Genera además los cambios en CSS + renderDetail para mostrar las nuevas métricas.
# --------------------

import json
import re
from pathlib import Path

QMD_OL/home/esp9221/PERM/pred-estacional/D  = Path("embalses.qmd")
JSON_/home/esp9221/PERM/pred-estacional/NEW = Path("embalses_data_v2.json")
QMD_/home/esp9221/PERM/pred-estacional/OUT  = Path("embal
ses_v2.qmd")

# Leer
with open(QMD_OLD, "r", encoding="utf-8") as f:
    qmd_text = f.read()

with open(JSON_NEW, "r", encoding="utf-8") as f:
    data_new = json.load(f)

# Serializar el JSON nuevo en formato compacto (igual que el original)
data_new_str = json.dumps(data_new, ensure_ascii=False, separators=(',', ':'))

# 1) Sustituir EMBALSES_DATA inline
qmd_new = re.sub(
    r'const EMBALSES_DATA = \[.*?\];',
    f'const EMBALSES_DATA = {data_new_str};',
    qmd_text,
    count=1,
    flags=re.DOTALL
)

# 2) Añadir CSS del bloque MEDSCOPE (antes de </style>)
css_medscope = """
.emb-medscope-section {
  background: linear-gradient(to right, #f4f8fd, #fff7ed);
  border: 1px solid #dde3ed;
  border-radius: 8px;
  padding: 0.9rem;
  margin: 1rem 0;
}
.emb-medscope-title {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; color: #003087; margin-bottom: 0.7rem;
}
.emb-medscope-row {
  display: grid;
  grid-template-columns: 80px 1fr 1fr 80px;
  gap: 0.4rem; align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.72rem;
}
.emb-medscope-label { font-weight: 600; color: #4a5568; }
.emb-medscope-bar-bg {
  height: 12px; background: #f0f4f8; border-radius: 99px;
  position: relative; overflow: hidden;
}
.emb-medscope-bar-fill {
  height: 100%; border-radius: 99px;
  position: absolute; top: 0;
}
.emb-medscope-vals {
  display: flex; gap: 0.4rem; font-size: 0.68rem;
  justify-content: flex-end; align-items: center;
}
.emb-medscope-val-orig { color: #2563eb; font-weight: 600; }
.emb-medscope-val-qdm  { color: #dc2626; font-weight: 700; }
"""
qmd_new = qmd_new.replace("</style>", css_medscope + "\n</style>", 1)

# 3) Añadir las dos funciones helper JS después de rBadge
helper_js = """

function fmt2s(v) {
  if (v == null) return '—';
  return (v >= 0 ? '+' : '') + v.toFixed(2);
}
function medscopeBarRow(label, orig, qdm, refLine, scaleMin, scaleMax) {
  const range = scaleMax - scaleMin;
  const refPct = ((refLine - scaleMin) / range) * 100;
  const origPct = orig != null ? Math.max(0, Math.min(100, ((orig - scaleMin) / range) * 100)) : 0;
  const qdmPct  = qdm  != null ? Math.max(0, Math.min(100, ((qdm  - scaleMin) / range) * 100)) : 0;
  return `
    <div class="emb-medscope-row">
      <span class="emb-medscope-label">${label}</span>
      <div class="emb-medscope-bar-bg">
        <div class="emb-medscope-bar-fill" style="width:${origPct}%;background:#93c5fd;opacity:0.75"></div>
        <div style="position:absolute;top:0;left:${refPct}%;width:1px;height:100%;background:#dc2626;"></div>
      </div>
      <div class="emb-medscope-bar-bg">
        <div class="emb-medscope-bar-fill" style="width:${qdmPct}%;background:#fca5a5;opacity:0.85"></div>
        <div style="position:absolute;top:0;left:${refPct}%;width:1px;height:100%;background:#dc2626;"></div>
      </div>
      <div class="emb-medscope-vals">
        <span class="emb-medscope-val-orig">${fmt2s(orig)}</span>
        <span class="emb-medscope-val-qdm">${fmt2s(qdm)}</span>
      </div>
    </div>`;
}
"""
qmd_new = re.sub(
    r"(function rBadge\(r\) \{[^}]*\})",
    r"\1" + helper_js,
    qmd_new,
    count=1
)

# 4) En renderDetail, generar medscopeHtml antes de panel.innerHTML
medscope_block = """
  // ── Bloque MEDSCOPE (ORIG vs QDM) ──
  let medscopeHtml = '';
  if (e.r_QDM != null) {
    medscopeHtml = `
      <div class="emb-medscope-section">
        <div class="emb-medscope-title">Verificación tipo MEDSCOPE — ORIG vs QDM</div>
        <div class="emb-medscope-row" style="border-bottom:1px solid #dde3ed;padding-bottom:0.3rem;margin-bottom:0.5rem;font-weight:700;">
          <span style="color:#003087;">Métrica</span>
          <span style="color:#2563eb;text-align:center;">ORIG</span>
          <span style="color:#dc2626;text-align:center;">QDM</span>
          <span></span>
        </div>
        ${medscopeBarRow('r',         e.r_orig,         e.r_QDM,         0,   -0.4, 0.6)}
        ${medscopeBarRow('BSS lower', e.BSS_lower_orig, e.BSS_lower_QDM, 0,   -1.0, 0.5)}
        ${medscopeBarRow('BSS upper', e.BSS_upper_orig, e.BSS_upper_QDM, 0,   -1.0, 0.5)}
        ${medscopeBarRow('AUC lower', e.AUC_lower_orig, e.AUC_lower_QDM, 0.5, 0.0,  1.0)}
        ${medscopeBarRow('AUC upper', e.AUC_upper_orig, e.AUC_upper_QDM, 0.5, 0.0,  1.0)}
        <div style="font-size:0.65rem;color:#6b7280;margin-top:0.4rem;text-align:right;font-style:italic;">
          Línea roja: referencia (climatología=0 para BSS, azar=0.5 para AUC)
        </div>
      </div>`;
  }

  """
qmd_new = qmd_new.replace(
    "  panel.innerHTML = `",
    medscope_block + "panel.innerHTML = `",
    1
)

# 5) Insertar ${medscopeHtml} antes de ${imgHtml} en el template
qmd_new = qmd_new.replace(
    "    ${imgHtml}`;",
    "    ${medscopeHtml}\n    ${imgHtml}`;",
    1
)

# Guardar
with open(QMD_OUT, "w", encoding="utf-8") as f:
    f.write(qmd_new)

print(f"Generado: {QMD_OUT}")
print(f"Tamaño: {QMD_OUT.stat().st_size / 1024:.0f} KB")